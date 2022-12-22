# =======================================================================================
# Simple utility for making a new user profile, for example
# =======================================================================================

import rsa
import json

userID = "example-user"
checkPhrase = "albatros"

publicKey, privateKey = rsa.newkeys(1024)
pub1 = publicKey.save_pkcs1()
prv2 = privateKey.save_pkcs1()

pubFP = open('./access-profiles/encrypt-{}.pem'.format(userID), 'wb')
pubFP.write(pub1)
pubFP.flush()
pubFP.close()

prvFP = open('./access-profiles/decrypt-{}.pem'.format(userID), 'wb')
prvFP.write(prv2)
prvFP.flush()
prvFP.close()

userProfile = {
    "user-id":userID,
    "check-phrase":"{}".format(checkPhrase),
    "decryption-url":'{}'.format('./access-profiles/decrypt-{}.pem'.format(userID))
}

dataProfileData = json.dumps(userProfile, indent=3)
dataProfileFP = open('./access-profiles/{}-profile.json'.format(userID), 'w')
dataProfileFP.write(dataProfileData)
dataProfileFP.flush()
dataProfileFP.close()
