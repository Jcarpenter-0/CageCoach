import requests
import json
import rsa
import datetime
from PIL import Image

# ======================================================================================================================
# Client for testing/showing data access systems
# ======================================================================================================================
RequesterID = 'example-user'
RequestorPhrase = 'albatros'
RequestorEncryptKeyPath = './access-profiles/encrypt-example-user.pem'
DebugDecryptorKeyPath = './access-profiles/decrypt-example-user.pem'
soughtDataURL = "http://localhost/6032024045f1dd3977ca9aade3ecc07f42f49719-data-descriptor.json"

# ======================================================================================================================

startTS = datetime.datetime.now()

# Get the data's owner information
dataRequestResponse = requests.get(soughtDataURL)
dataRequestResponseDict = json.loads(dataRequestResponse.text)

# Ask the owner for access to that data
encryptFP = open(RequestorEncryptKeyPath, 'rb')
encryptKeyRaw = encryptFP.read()
encryptFP.close()
publicKey = rsa.PublicKey.load_pkcs1(encryptKeyRaw)
encryptedData = rsa.encrypt(RequestorPhrase.encode(), publicKey)

#decryptFP = open(DebugDecryptorKeyPath, 'rb')
#decryptKeyRaw = decryptFP.read()
#decryptFP.close()
#prvKey = rsa.PrivateKey.load_pkcs1(decryptKeyRaw)
#decryptedData = rsa.decrypt(encryptedData, prvKey)

requestParameters = {'request-url':dataRequestResponseDict['data-url'],'user-id':RequesterID, 'user-phrase':encryptedData.hex()}

ownerRequestResponse = requests.post(dataRequestResponseDict['owner-url'] + '/request-data', requestParameters)

# Save off the data for a second
requestedDataFP = open('requested-data.{}'.format('json'), 'wb')
requestedDataFP.write(ownerRequestResponse.content)
requestedDataFP.flush()
requestedDataFP.close()

endTS = datetime.datetime.now()
timeDelta = endTS - startTS
timeTakenMicroSeconds = timeDelta.microseconds

print('Data Transaction {} ns'.format(timeTakenMicroSeconds))