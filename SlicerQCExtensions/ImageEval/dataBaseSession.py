import urllib
from xml.etree import ElementTree as et
from glob import glob
import os
import random
import parseXML

class DataBaseSession():

  def __init__(self, basePath, database, questionsList, username=None, password=None):
    self.basePath = basePath
    self.database = database
    self.questionsList = questionsList
    self.username = username
    self.password = password

    # xmlString = self.getXMLstring()

    with open('/tmp/xmlStringExample.xml','r') as handle:
      xmlString = handle.read()

    self.notReviewedList = self.createUnreviewedScansList(xmlString)
    self.currentScan = self.setCurrentScan()
    print self.notReviewedList

  def getRandomUnreviewedScan(self):
    if len(self.notReviewedList) == 0:
      return False
    else:
      randomNumber = random.randrange(0, len(self.notReviewedList))
      val = self.notReviewedList.pop(randomNumber)
      return val

  def setCurrentScan(self):
    return self.getRandomUnreviewedScan()

  def getCurrentScan(self):
    return self.currentScan

class XNATDataBaseSession(DataBaseSession):

  def getXMLstring(self):
    """
    Copy the Image Eval XML information from XNAT.
    Store it in the string "xmlString"
    """
    restURL = self.getRestURL()
    url = "https://{0}:{1}@{2}".format(self.username, self.password, restURL)
    info = urllib.urlopen(url)
    xml_string = info.read()
    return xml_string

  def getRestURL(self):
    projectReq = "{HOSTURL}/xnat/REST/custom/scans?type=(T1|T2|PD|PDT2)-(15|30)&format=xml".format(HOSTURL=self.database)
    return projectReq

  def createUnreviewedScansList(self, xmlString):
    root = et.fromstring(xmlString)
    notReviewedList = list()
    columnList = self.getColumnList(root)
    for row in root.iter('row'):
      reviewedIndex = columnList.index('reviewed')
      reviewed = row[reviewedIndex].text
      if reviewed != 'Yes':
        scan = XNATScanObject(row, columnList, self.basePath, self.questionsList)
        notReviewedList.append(scan)
    return notReviewedList

  def getColumnList(self, root):
    columnList = list()
    columnElements = root.findall('results/columns/column')
    for elem in columnElements:
      columnList.append(elem.text)
    return columnList

class ScanObject():

  def __init__(self, rowElement, columnList, basePath, questionsList):
    self.rowElement = rowElement
    self.columnList = columnList
    self.basePath = basePath
    self.questionsList = questionsList
    self.parseXML()
    self.filePath = self.createFilePath()
    self.label = self.createLabel()
    self.ReviewXMLObject = self.createReviewXML()

  def getSession(self):
    return self.session

  def getProject(self):
    return self.project

  def getSubject(self):
    return self.subject

  def getSeriesNumber(self):
    return self.seriesnumber

  def getType(self):
    return self.type

  def getReviewedFlag(self):
    return self.reviewed

  def createFilePath(self):
    filename = "{0}_{1}_{2}_{3}.nii.gz".format(self.subject, self.session,
                                               self.type, self.seriesnumber)
    pattern = os.path.join(self.basePath, self.project, self.subject, self.session,
                           'ANONRAW', filename)
    try:
      return glob(pattern)[0]
    except IndexError as e:
      print("File not found at path: {0} ".format(pattern))
      return "Not Found"
    except:
      return "Invalid"

  def getFilePath(self):
    return self.filePath

  def createLabel(self):
    return "{0}_{1}_IR".format(self.session, self.seriesnumber)

  def getReviewXMLObject(self):
    return self.ReviewXMLObject

class XNATScanObject(ScanObject):

  def parseXML(self):
    self.project = self.setVariable('project')
    self.subject_id = self.setVariable('subject_id')
    self.subject = self.setVariable('subject')
    self.sessionID = self.setVariable('session_id')
    self.session = self.setVariable('session')
    self.date = self.setVariable('date')
    self.time = self.setVariable('time')
    self.seriesnumber = self.setVariable('seriesnumber')
    self.type = self.setVariable('type')
    self.quality = self.setVariable('quality')
    self.reviewed = self.setVariable('reviewed')
    self.status = self.setVariable('status')
    self.element_name = self.setVariable('element_name')
    self.insert_date = self.setVariable('insert_date')
    self.activation_date = self.setVariable('activation_date')
    self.last_modified = self.setVariable('last_modified')

  def setVariable(self, val):
    i = self.columnList.index(val)
    return self.rowElement[i].text

  def createReviewXML(self):
    return parseXML.XnatReviewXML(self.project, self.label, self.questionsList)

  def makePostEvaluationURL(self, hostURL):
    url = "{HOSTURL}/xnat/REST/projects/{PROJECT}/subjects/{SUBJECT}/experiments" \
          "/{SESSION}/assessors/{ASSESSOR}&xsiType=phd:ImageReviewData".format(
      HOSTURL=hostURL, PROJECT=self.project, SUBJECT=self.subject, SESSION=self.session, ASSESSOR=self.label)
    print '#'*50
    print url
    print '#'*50
    return url

if __name__ == "__main__":
  imageEvalQuestionnaireFilePath = "/IPLlinux/raid0/homes/jforbes/git/WorkInProgress/SlicerQCExtensions/ImageEval/ImageEvalQuestionnaire.xml"
  QuestionnaireXMLObject = parseXML.ParseXML(imageEvalQuestionnaireFilePath)
  questionnaireList = QuestionnaireXMLObject.getQuestionsList()
  Object = XNATDataBaseSession('/Shared/johnsonhj/TrackOn', questionnaireList)
  unreviewedScan = Object.getRandomUnreviewedScan()
