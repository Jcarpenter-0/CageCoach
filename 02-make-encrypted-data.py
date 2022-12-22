# =======================================================================================
# Simple utility for encrypting data and stamping a data profile and description for it
# =======================================================================================

from cryptography.fernet import Fernet
import rsa
import json
import os
import hashlib

# =======================================================================================
#
# =======================================================================================
dataFilePath = './data/example-data.json'

# =======================================================================================
fullyQualifiedName = dataFilePath.split('/')[-1]
justFileName = os.path.basename(dataFilePath).split('.')[0]
fileExtension = dataFilePath.split('.')[-1]

dataFileDataFP = open(dataFilePath, 'rb')
rawFileData = dataFileDataFP.read(os.path.getsize(dataFilePath))
dataFileDataFP.close()

key = Fernet.generate_key()
f = Fernet(key)
encMessage = f.encrypt(rawFileData)

fileHash = hashlib.sha1(encMessage)
fileHashString = fileHash.hexdigest()

encDataFP = open('./data/{}-data'.format(fileHashString), 'wb')
encDataFP.write(encMessage)
encDataFP.flush()
encDataFP.close()

# === Old RSA approach, only good for smaller files, but otherwise robust! ==========
# Prepare new encryption key

#publicKey, privateKey = rsa.newkeys(323056, poolsize=4)
#pub1 = publicKey.save_pkcs1()
#prv2 = privateKey.save_pkcs1()

# Encrypt the file
#encMessage = rsa.encrypt(rawFileData,publicKey)
#fileHash = hashlib.sha1(encMessage)
#fileHashString = fileHash.hexdigest()
#encDataFP = open('./data/{}-data'.format(fileHashString), 'wb')
#encDataFP.write(encMessage)
#encDataFP.flush()
#encDataFP.close()

#pubFP = open('./data-profiles/encrypt-{}.pem'.format(fileHashString), 'wb')
#pubFP.write(pub1)
#pubFP.flush()
#pubFP.close()

#prvFP = open('./data-profiles/decrypt-{}.pem'.format(fileHashString), 'wb')
#prvFP.write(prv2)
#prvFP.flush()
#prvFP.close()


# =======================================================================================================
# Write out the key and other information
# =======================================================================================================

keyFP = open('./data-profiles/{}-key'.format(fileHashString), 'wb')
keyFP.write(key)
keyFP.flush()
keyFP.close()


dataProfile = {
    "meta-data":["data", "textual", "json"],
    "original-data-name":fullyQualifiedName,
    "data-type":"{}".format(fileExtension),
    "data-url":"http://localhost/{}-data".format(fileHashString),
    "encryption-key-path":'{}'.format('./data-profiles/{}-key'.format(fileHashString))
}

dataProfileData = json.dumps(dataProfile, indent=3)
dataProfileFP = open('./data-profiles/{}-data-profile.json'.format(fileHashString), 'w')
dataProfileFP.write(dataProfileData)
dataProfileFP.flush()
dataProfileFP.close()

dataDescriptor = {
    "owner-url": "http://localhost:9090/",
    "meta-data": ["data", "textual", "json"],
    "description": "This is some sample text data.",
    "data-url": "http://localhost/{}-data".format(fileHashString),
    "data-hash-{}".format(fileHash.name): fileHashString
}

dataDescriptorData = json.dumps(dataDescriptor, indent=3)
dataDescriptorDataFP = open('./data/{}-data-descriptor.json'.format(fileHashString), 'w')
dataDescriptorDataFP.write(dataDescriptorData)
dataDescriptorDataFP.flush()
dataDescriptorDataFP.close()