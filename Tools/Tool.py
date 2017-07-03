#-*- coding: utf-8 -*-
from zipfile import BadZipFile

try:
    import zipfile
    import os
    import shutil
    import tempfile
    import re
    import patoolib
    from pyunpack import Archive
    import time
    from tkinter import *

except ImportError:
    raise ImportError("Missing packages")

class Tool:
    def __init__(self):
        self.lIsCompressed     = []
        self.lReplace          = []

        self.Pattern           = {}

        self.pDigit        = re.compile("[0-9]+")
        self.pOneLetter    = re.compile("[A-Z]{1}[0-9]+")
        self.pMoreLetter   = re.compile("[A-Z]{2,5}[0-9]+")
        self.pMatchAll     = re.compile("[A-Z0-9-._]+")

        self.curZip        = 0
        self.curDB         = 0

    def getTotalFolder(self, dirPath):
        numZip  = self.getTotalZip(dirPath)
        numPDF  = self.getTotalPDF(dirPath)
        numExcl = self.getExcludedFile(dirPath)
        return len(os.listdir(dirPath)) - (numZip + numPDF + numExcl)

    def getTotalZip(self, dirPath):
        filterList = list(filter(lambda x: '.zip' in x, os.listdir(dirPath)))
        return len(filterList)

    def getTotalPDF(self, dirPath):
        filterList = list(filter(lambda x: '.pdf' in x, os.listdir(dirPath)))
        return len(filterList)

    def getExcludedFile(self, dirPath):
        num = 0
        for ext in ['test', 'test.txt', 'fav.txt', 'Guro']:
            num += 1 if os.path.exists(dirPath + ext) else 0
        return num

    def getCurrentDB(self):
        return self.curDB

    def getCurrentZip(self):
        return self.curZip

    def isEnglish(self, string):
        # function to detect if a string is English or not
        try:
            string.encode('ascii')
        except UnicodeEncodeError:
            return False
        else:
            return True

    def createDatabase(self, dirPath, dbName):
        # Fuction to store the downloaded files to a single text file for searching

        self.removeIfExist(dirPath + dbName)

        f = open(dirPath + '/' + dbName, mode='wb')
        for file in os.listdir(dirPath):
            # file = tmpFile.decode('UTF-8')
            tmpList = file.split('.')
            iPage   = 0
            if len(tmpList) > 1 and tmpList[len(tmpList)-1] in ['zip','pdf']:
                sLang = 'Eng'
                fStat = os.stat(dirPath + file)
                fSize = fStat.st_size
                fSize = round((fSize / (1024 ** 2)),2)
                # Get created time
                cTime = time.ctime(fStat.st_ctime)

                # Encode in utf-8 then write to file under binary format.
                # Decode before reading to get the original form.
                if not self.isEnglish(file[:-4]):
                    sLang = 'Jap'
                if tmpList[len(tmpList)-1] == 'zip':
                    try:
                        with zipfile.ZipFile(dirPath + '/' + file, 'r') as zipRead:
                            iPage = len(zipRead.infolist())
                    except BadZipFile:
                        print(file)
                        continue
                if type(file) != bytes:
                    file = file.encode('utf-8')
                # The database entry: <filename>,<language>,<number of pages>
                # f.write('%s,%s,%sMB,%s\n' % (file[:-4], sLang, fSize, len(zipRead.infolist())))

                tmpStr = ('#' + sLang + '#' + str(fSize) + 'MB#' + str(iPage) + '#' + cTime + '\r\n').encode('utf-8')
                f.write(file[:-4] + tmpStr)
                self.curDB += 1

        f.close()
        print('Finished')

    def readDB(self, filePath):
        # Function to read detail info inside DB file and put into a dictionary
        # return { title : { size: <> , lang: <>, pages: <> }
        dData = {}

        try:
            with open(filePath, 'rb') as fRead:
                for line in fRead.readlines():
                    line = line.decode('utf-8')
                    line = line.replace('\r\n','')
                    entry = line.split('#')
                    if len(entry) == 5: # Normal entry without a comment.
                        entry.append('Not Added')
                    dData.update({entry[0] : {'lang': entry[1], 'size': entry[2], 'page': entry[3], 'ctime': entry[4], 'cmt': entry[5]}})
        except FileNotFoundError:
            raise FileNotFoundError("File %s not found" % filePath)

        return dData

    def compressSeparateFolder(self, dirPath, textWg):
        # Function to compress folder in a directory to separate .zip file.
        # Except: compressed files.
        self.listCompressed(dirPath)
        count = 0
        for folder in os.listdir(dirPath):

            if folder[-3:] in ['zip', '.py', 'rar', 'pdf', 'txt'] or folder in ['Guro', 'test']:
                continue
            else:
                if folder + '.zip' not in self.lIsCompressed:
                    zipName = zipfile.ZipFile('{0}.zip'.format(os.path.join(dirPath, folder)), 'w',
                                              zipfile.ZIP_DEFLATED)
                    for root, dirs, files in os.walk(dirPath + '/' + folder):
                        for file in files:
                            zipName.write(os.path.abspath(os.path.join(root, file)), arcname = file)
                    zipName.close()
                    count += 1
                    textWg.insert(END, folder + ' ==> Done compressed. Total: %s\n' % str(count))
                    textWg.see(END)

                    self.curZip += 1

                    self.removeFolder(dirPath + '/' + folder)

    def listCompressed(self, dirPath):
        for folder in os.listdir(dirPath):
            if folder[-3:] == 'zip':
                self.lIsCompressed.append(folder)

    def listEverything(self, dirPath):
        # List all file in an archive
        for file in os.listdir(dirPath):
            if 'zip' in file:
                print('-- %s \n' % file)
                with zipfile.ZipFile(dirPath + file, 'r') as zipRead:
                    for item in zipRead.infolist():
                        print('->> %s' % item.filename)

    def unRar(self, dirPath, destPath):
        # Function to unrar .rar file.
        for folder in os.listdir(dirPath):
            if folder[-3:] == 'rar':
                Archive(dirPath + '/' + folder).extractall(destPath)
                print('Done unRAR %s' % folder)
                shutil.rmtree(dirPath + '/' + folder)

    def removeFolder(self, dirPath):
        # Function to remove already compressed folder to save space
        shutil.rmtree(dirPath, ignore_errors= True)

    def removeIfExist(self, filePath):
        # Function to check if a file existed, remove if Yes.
        if os.path.exists(filePath):
            os.remove(filePath)

    def getCommonPattern(self, dirPath):
        # Function to summarize general pattern of picture file
        self.Pattern = {'digit'     : 0,
                        'oneLetter' : 0,
                        'moreLetter': 0,
                        'matchAll'  : 0,
                        'UI'        : []}
        iCount = 100
        for file in os.listdir(dirPath):
            if iCount == 0:
                break
            if 'zip' in file:
                with zipfile.ZipFile(dirPath + file, 'r') as zipRead:
                    for item in zipRead.infolist():
                        if self.pDigit.match(item.filename):
                            self.Pattern['digit'] += 1
                            iCount -= 1
                            break
                        elif self.pOneLetter.match(item.filename):
                            self.Pattern['oneLetter'] += 1
                            iCount -= 1
                            break
                        elif self.pMoreLetter.match(item.filename):
                            self.Pattern['moreLetter'] += 1
                            iCount -= 1
                            break
                        elif self.pMatchAll.match(item.filename):
                            self.Pattern['matchAll'] += 1
                            iCount -= 1
                            break
                        else:
                            self.Pattern['UI'].append(item.filename)
                            iCount -= 1
                            break

        dPattern = self.Pattern
        return dPattern

    def checkContentofArchive(self, zipFolder, pattern):
        # Function to check the content of a zip archive if follow a defined pattern
        # Return True / False
        iMisMatch = 0 # If pattern not match, count until reach a define number, here we can decide not to continue
        iMatch    = 0

        with zipfile.ZipFile(zipFolder, 'r') as zipRead:
            for item in zipRead.infolist():
                if iMisMatch > 5:
                    return False
                if pattern.match(item.filename):
                    iMatch += 1
                    if iMatch > 5:
                        return True
                else:
                    iMisMatch += 1

        return True

    def checkStringPortion(self, sOrigin, sNew):
        """
        Function to check how many percent new String match an origin one
        :param sOrigin:
        :param sNew:
        :return: Percent in int
        """
        total = len(sOrigin)
        percent = 0
        for i in range(len(sNew)):
            if sNew[i] == sOrigin[i]:
                percent += 1
        return (percent / total) * 100

    def checkContentofFolder(self, folder, pattern):
        '''
        Function to check the content of a zip archive if follow a defined pattern
        :param folder:
        :param pattern:
        :return: True if match aka skip, False if not aka rename
        '''
        iMisMatch = 0  # If pattern not match, count until reach a define number, here we can decide not to continue
        iMatch    = 0
        for item in os.listdir(folder):
            if iMisMatch > 5:
                return False

            if not re.match("[0-9]+", item[:-4]):
                if self.checkStringPortion(pattern, item[:-4]) > 50:
                    iMatch += 1
                    if iMatch > 5:
                        return True
                else:
                    iMisMatch += 1
            else:
                iMisMatch += 1
        return False

    def replaceFileInFolder(self, folderPath):
        # Function to replace a file in a folder
        for folder in os.listdir(folderPath):
            # lTemp = folderPath.split('/')
            titleName = folder

            if titleName[:4] in ['test', 'Guro']:
                continue
            if not self.checkContentofFolder(folderPath + folder, titleName):
                for item in os.listdir(folderPath + folder):
                    numOrder = re.search("\d+", item).group()
                    ext      = item[-4:]
                    newName = titleName + '_' + numOrder + ext
                    os.rename(folderPath + folder + '\\' + item, folderPath + folder + '\\' + newName)

    def replaceFileInZip(self, zipPath, pattern):
        #TODO: not good enough. File name is too complicated.
        # Function to replace a file in an archive
        lTemp   = zipPath.split('/')
        zipName = lTemp[len(lTemp) - 1]

        if 'zip' in zipName:
            if self.checkContentofArchive(zipPath, pattern):
                tmpDir  = tempfile.mkdtemp()
                tmpName = os.path.join(tmpDir, 'new.zip')

                with zipfile.ZipFile(zipPath, 'r') as zipRead:
                    with zipfile.ZipFile(tmpName, 'w') as zipWrite:
                        for item in zipRead.infolist():
                            newName = zipName + '_' + item.filename
                            zipWrite.writestr(newName, zipRead.read(item.filename))

                shutil.move(tmpName, zipPath)
        else:
            print('%s not compressed yet' % zipName)

    def replaceFile(self, dirPath):
        # General function to make change to a file (in folder before compressing)
        #TODO: incomplete.
        lTmp = dirPath.split('/')
        tmpFile = lTmp[len(lTmp) - 1]

        self.replaceFileInFolder(dirPath)