# =================================================================
# System that controls access to data it is in charge of.
#
#
# =================================================================
import ast
import os
import shutil
import sys
import json
import glob
import requests
import pandas as pd
import rsa
import http.server
import cv2
import urllib.parse
from cryptography.fernet import Fernet

import data_pipeline

import a_type_specific_redact_ops
import b_data_specific_redact_ops
import c_user_specific_redact_ops

# Server Globals
DataRequestCommandPath = '/request-data'
ProfileRequestCommandPath = '/access-profile'
DataProfiles = './data-profiles/'
RequestAccessProfiles = './access-profiles/'


def VerifyUser(userID, userEncryptedPhrase) -> bool:

    requesterAccessProfiles = glob.glob(RequestAccessProfiles + '*.json')

    userVerified = False

    for profile in requesterAccessProfiles:

        profileFP = open(profile, 'rb')
        requesterProfileDict = json.load(profileFP)
        profileFP.close()

        if requesterProfileDict['user-id'] == userID:

           # load decrypt key
           decryptFP = open(requesterProfileDict['decryption-url'], 'rb')
           decryptData = decryptFP.read()
           decryptFP.close()

           privateKey = rsa.PrivateKey.load_pkcs1(decryptData)
           phraseBytes = bytes.fromhex(userEncryptedPhrase)
           decryptedData = rsa.decrypt(phraseBytes, privateKey).decode()

           if decryptedData == requesterProfileDict['check-phrase']:
               userVerified = True
               return userVerified

    return userVerified


class DataControlHTTPHandler(http.server.SimpleHTTPRequestHandler):

    # POST - Receive commands to execute
    def do_POST(self):
        """
        Respond to POST requests with "data", "profile for data access"
        """

        responseCode = 200
        contentType = 'application/json'
        dataPayload: bytes = 'Filler'.encode()

        try:
            itemPath = self.path

            # Parse out necessary parameters
            length = int(self.headers['content-length'])
            postDataRaw = self.rfile.read(length)
            postDataDict = urllib.parse.parse_qs(str(postDataRaw,"UTF-8"))

            # Verify the user
            userVerified = False

            if 'user-id' in postDataDict.keys() and 'user-phrase' in postDataDict.keys():
                try:
                    userVerified = VerifyUser(postDataDict['user-id'][0], postDataDict['user-phrase'][0])
                except Exception as inputEx:
                    responseCode = 400
                    dataPayload = "{\"message\":\"Parameters incorrect.\"}".encode()
                    raise inputEx

            if DataRequestCommandPath in itemPath:

                dataHash = None

                try:
                    # Check if inputs are proper
                    dataHash = postDataDict['request-url'][0].split('/')[-1]
                except Exception as inputEx:
                    responseCode = 400
                    dataPayload = "{\"message\":\"Parameters incorrect.\"}".encode()
                    raise inputEx

                # Is this data owned by this DCS?
                dataProfiles = glob.glob(DataProfiles + '*.json')

                # Locate possible data profile
                for dataProfile in dataProfiles:
                    if dataHash in dataProfile:
                        profileDataFP = open(dataProfile, 'rb')
                        profileDataDict = json.load(profileDataFP)
                        profileDataFP.close()

                        # ======aquire data to decrypt, this can be hosting APIs too=======================================
                        dataReqResp = requests.get(profileDataDict['data-url'])
                        # =================================================================================================

                        if dataReqResp.status_code == 200:
                            # decrypt the data
                            decryptFP = open(profileDataDict['encryption-key-path'], 'rb')
                            decryptData = decryptFP.read()
                            decryptFP.close()

                            decryptKey = Fernet(decryptData)
                            decryptedData = decryptKey.decrypt(dataReqResp.content)


                            tmpFileName = './tmp-file.{}'.format(profileDataDict['data-type'])
                            tmpFile = open(tmpFileName, 'wb')
                            tmpFile.write(decryptedData)
                            tmpFile.flush()
                            tmpFile.close()

                            requestedItemDataType = profileDataDict['data-type']
                            requestedItemOriginalDataName = profileDataDict['original-data-name']

                            # Aquire the redaction operations for the user (if supplied), the data type, and the specific data item
                            redactionOperations = []

                            if requestedItemDataType in a_type_specific_redact_ops.dataTypeSpecificRedactOps.keys():
                                topLevelRedactions = a_type_specific_redact_ops.dataTypeSpecificRedactOps[requestedItemDataType]
                                redactionOperations.extend(topLevelRedactions)

                            if requestedItemOriginalDataName in b_data_specific_redact_ops.dataSpecificRedactOps.keys():
                                midLevelRedactions = b_data_specific_redact_ops.dataSpecificRedactOps[requestedItemOriginalDataName]
                                redactionOperations.extend(midLevelRedactions)

                            if userVerified and postDataDict['user-id'][0] in c_user_specific_redact_ops.userSpecificRedactOps.keys():
                                lowLevelRedactions = c_user_specific_redact_ops.userSpecificRedactOps['{}|{}'.format(postDataDict['user-id'][0],requestedItemDataType)]
                                redactionOperations.extend(lowLevelRedactions)

                            if requestedItemDataType == 'blob':
                                contentType = 'text/plain'
                                dataPayload = decryptedData

                            elif requestedItemDataType == 'json':
                                contentType = 'application/json'
                                rawData = json.loads(decryptedData.decode())

                                for op in redactionOperations:
                                    rawData = op.Operate(rawData)

                                dataPayload = json.dumps(rawData, indent=3).encode()

                            elif requestedItemDataType == 'csv':
                                contentType = 'text/csv'
                                rawData = pd.read_csv(tmpFileName)

                                for op in redactionOperations:
                                    rawData = op.Operate(rawData)

                                # output the file back to the tmp, then reload it as bytes for sending
                                rawData.to_csv(tmpFileName, index=False)
                                rawFileDataFP = open(tmpFileName, 'rb')
                                dataPayload = rawFileDataFP.read()
                                rawFileDataFP.close()

                            elif requestedItemDataType == 'mp3' or requestedItemDataType == 'wav':
                                pass

                            elif requestedItemDataType == 'jpg' or requestedItemDataType == 'png':
                                contentType = 'image/jpeg'

                                rawData = cv2.imread(tmpFileName)

                                # do redact, then return
                                for op in redactionOperations:
                                    rawData = op.Operate(rawData)

                                # Save image, to then reload as bytes for sending
                                cv2.imwrite(tmpFileName, rawData)

                                tmpImageFP = open(tmpFileName, 'rb')
                                rawBytesOfData = tmpImageFP.read()
                                tmpImageFP.close()

                                dataPayload = rawBytesOfData

                            # Delete the temp file
                            os.remove(tmpFileName)

                        else:
                            # could not aquire the data
                            responseCode = 404
                            dataPayload = "{\"message\":\"Could not locate the data item.\"}".encode()
                            raise Exception('Could not locate data item')

                        # Step out of the profile searching loop
                        break

            elif ProfileRequestCommandPath in itemPath:
                pass
            else:
                responseCode = 404
        except Exception as overallException:
            print(overallException)

        # set HTTP headers
        self.send_response(responseCode)
        self.send_header('Content-Type', contentType)
        self.send_header('Content-Length', '{}'.format(len(dataPayload)))
        self.end_headers()

        # Finish web transaction
        self.wfile.write(dataPayload)


class DataControlServer(object):
    def __init__(self, serverAddress, port):
        self.serverAddress = (serverAddress, port)
        self.httpd = http.server.HTTPServer(self.serverAddress, DataControlHTTPHandler)

    def run(self):
        cont = True

        while(cont):
            try:
                self.httpd.serve_forever()
            except KeyboardInterrupt:
                cont = False
            except Exception as ex:
                print(ex)

    def cleanup(self):
        self.httpd.shutdown()


if __name__ == '__main__':

    port = int(sys.argv[1])
    address = ''
    try:
        address = sys.argv[2]
    except:
        pass

    # ==============================
    # Startup the server
    # ==============================

    webserver = DataControlServer(address, port)

    try:
        webserver.run()
    except KeyboardInterrupt:
        print()
    except Exception as ex:
        print()
    finally:
        webserver.cleanup()