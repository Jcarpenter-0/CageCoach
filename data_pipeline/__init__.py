# =====================================================================
#
# =====================================================================
from typing import List
import pandas as pd
from PIL import Image
import pytesseract
import cv2


class JsonOps():

    def __init__(self, fieldsToDrop:List[str], valuesToDrop:list, subsetDrops:bool=False):
        self.FieldsToDrop = fieldsToDrop
        self.ValuesToDrop = valuesToDrop
        self.SubsetDrops = subsetDrops

    def Operate(self, data:dict) -> dict:

        for fieldToDrop in self.FieldsToDrop:
            del data[fieldToDrop]

        for field in data.keys():
            if self.SubsetDrops:
                for valueToDrop in self.ValuesToDrop:
                    data[field] = '{}'.format(data[field]).replace('{}'.format(valueToDrop),'x')
            else:
                if data[field] in self.ValuesToDrop:
                    data[field] = None

        return data

class PandasOps():

    def __init__(self, columnsToRemove:List[str], valuesToRemove:list):
        self.ColumnsToRemove = columnsToRemove
        self.ValuesToRemove = valuesToRemove

    def Operate(self, data:pd.DataFrame) -> pd.DataFrame:

        subData:pd.DataFrame = data.drop(self.ColumnsToRemove, axis=1)

        for valueToRemove in self.ValuesToRemove:
            subData = subData.replace(valueToRemove, None)

        return subData

class ImageOps():

    def __init__(self):
        return

    def Operate(self, image:object) -> object:
        return


class Image_Redact_Faces(ImageOps):

    def __init__(self):
        """Code from https://www.geeksforgeeks.org/blur-and-anonymize-faces-with-opencv-and-python/"""
        super().__init__()
        return

    def Operate(self, image:object) -> object:
        cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

        # convert the frame into grayscale(shades of black & white)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detects multiple faces
        face = cascade.detectMultiScale(gray_image,
                                        scaleFactor=1.04,
                                        minNeighbors=4)

        for x, y, w, h in face:
            # draw a border around the detected face.
            # (here border color = green, and thickness = 3)
            subImage = cv2.rectangle(image, (x, y),
                                  (x + w, y + h),
                                  (0, 255, 0), 3)

            # blur the face which is in the rectangle
            subImage[y:y + h, x:x + w] = cv2.medianBlur(subImage[y:y + h, x:x + w], 35)

        return image


class AudioOps():

    def __init__(self, muteWords:bool, muteBackground:bool):
        self.MuteBackground = muteBackground
        self.MuteWords = muteWords

    def Operate(self, audio:object) -> object:

        if self.MuteWords:
            # identify words in sound file, mute them
            pass

        if self.MuteBackground:
            # apply background mute
            pass




        return