# ===================================================================================================================
# Specify here the ops that a specific data item should undergo, note: use the "real name" not the HASH
# ===================================================================================================================
# Format: "example-data.json":[Operation 1, Operation 2]

import data_pipeline

dataSpecificRedactOps = {"example-data.json":[data_pipeline.JsonOps(fieldsToDrop=['Name'], valuesToDrop=['2 inches'], subsetDrops=True)],
                         "smiling-buddha-example.jpg":[data_pipeline.Image_Redact_Faces()]}