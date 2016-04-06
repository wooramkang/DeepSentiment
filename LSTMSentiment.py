import cPickle,os
import Preprocessor as pp
import numpy
import re
from keras.models import Sequential
from keras.layers.core import Dense, Activation,Dropout,TimeDistributedDense
from keras.layers.recurrent import LSTM
from keras.layers.embeddings import Embedding

from sklearn import svm
from sklearn import cross_validation
from sklearn.multiclass import OneVsRestClassifier


class LSTMSentiment:

    def __init__(self):
       self.in_dim = 500
       self.n_prev=25
       self.future=50
       out_dim = 1
       hidden_neurons = 500
       self.max_length = 500
       max_features = 20000
       self.batch_size=50
       
       # Initializing a sequential Model
       self.model = Sequential()
       self.model.add(Embedding(max_features, 128, input_length=self.max_length))
       #self.model.add(LSTM(output_dim=128,input_dim=500,activation='relu'))
       self.model.add(LSTM(output_dim=128,activation ='sigmoid',return_sequences=True))
       self.model.add(Dropout(0.5))
       self.model.add(LSTM(400))
       #self.model.add(Activation("relu"))
       self.model.add(Dropout(0.5))
       self.model.add(Dense(1))
       self.model.add(Activation('tanh'))

       self.model1 = OneVsRestClassifier(svm.SVC(kernel='rbf',gamma=1,C = 1,tol=0.0001,cache_size=5000)  )


    def configureLSTMModel(self,TrainX,TrainY,validX,validY):
       print('Configuring the LSTM Model')
       self.model.compile(loss='binary_crossentropy', optimizer='rmsprop',class_mode="binary")
       #,class_mode ="binary")
       #self.model.fit(TrainX, TrainY, nb_epoch=5,batch_size=self.batch_size, show_accuracy=True,validation_data=(validX,validY))

       self.model1.fit(TrainX, TrainY)

    def evaluateLSTMModel(self,TestX,TestY):
       #obj_sc,acc = self.model.evaluate(TestX, TestY, batch_size=32,show_accuracy=True)
       # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
       # print('Objective Score : ',obj_sc)
       # print('Accuracy : ' ,acc)

       print self.model1.score(TestX, TestY)

       predicted_data=[]
       for i in range(len(TestX)):
          predicted_data.append(list([self.model1.predict(TestX[i].reshape(1,-1)),TestY[i]]))

       print "Predicted Data"
       print predicted_data
       #print TestY



    def predictSentiment(self,testX,testY):
       sentiment = self.model.predict_on_batch(testX)
       print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
       print(sentiment)
       print testY


    def getTrainTestData(self):
       print('Loading Training and Test data')
       trainX=[]
       trainY=[]
       testX=[]
       testY = []

       f= open('trainingdata.pkl','rb')
       (trainX,trainY) = cPickle.load(f)
       
       f= open('testingdata.pkl','rb')
       (testX,testY)  = cPickle.load(f)

       return ((trainX,trainY),(testX,testY))

    def build_dict(self,trainX,testX):
       sentences =[]
       sentences = trainX + testX
       wordCnt = dict()
       # Splitting each sentences into words and getting the word count.
       for i in sentences:
         words = i.lower().split()
         for w in words:
            if w not in wordCnt:
               wordCnt[w] = 1
            else:
               wordCnt[w] +=1

       counts = wordCnt.values()
       keys = wordCnt.keys()

       #print('############# Counts and Keys ################')
       #print(counts ,'::::::::: ',keys)

       sorted_idx = numpy.argsort(counts)[::-1]
       #print('################ SortedId ###################')
       #print(sorted_idx)

       worddict = dict()

       for idx, ss in enumerate(sorted_idx):
          worddict[keys[ss]] = idx+2

       print numpy.sum(counts), ' total words ', len(keys), ' unique words'

       return worddict

    # Transforms sentences into number vectors where number represents value corresponding to the word in the Dictionary built above
    def transformData(self,dataX,dataY,worddict):
       transformedDataX = [None] * len(dataX)
       transformedDataY = dataY
       for ind,sen in enumerate(dataX):
          #words = sen.lower().split()
          words = re.sub("[^\w]", " ", sen).lower().split()
          transformedDataX[ind]=[]
          for w in words:
             if w in worddict:
                transformedDataX[ind].append(worddict[w])
             else:
                transformedDataX[ind].append(1)
          
       #Converting the length of the transformed data to maximum length
       transX = []
       for i in transformedDataX:
          transLen = len(i)
          if(transLen < self.max_length): #Pad zeroes to the data vector
              transX.append([0]*(self.max_length - transLen) + i)
              #print('@@@@@@@@@@@@@@@@@@@ Test:  ',len(i), ' ; ',len(j) )
              #print(i)
          elif transLen > self.max_length:
              j = i
              del j[self.max_length:]
              transX.append(j)


          #transformedData[ind] = [worddict[w] if w in worddict else 1 for w in words]
       print('############################# Transformed Data ###################')
       print(transX)
       return (transX, transformedDataY)



    def prepareData(self,dataX):
       wordList=[]
       for i in xrange(0,len(dataX)):
          wordList[i] = re.sub("[^\w]", " ",  dataX[i]).split()
          print(dataX[i],' :::::::::::::::::::::   ',wordList[i])

    def getValidationData(self,dataX,dataY):

       return dataX[0:self.batch_size,:],dataY[0:self.batch_size,:]


def main():
   print('Initializing the LSTM Model')
   lstm = LSTMSentiment()
   
   print('Retrieving the Training and Test Data')
   path = os.getcwd()
   ((trainX,trainY),(testX,testY)) = lstm.getTrainTestData()



   worddict = dict()
   worddict = lstm.build_dict(trainX,testX)

   print('Transforming Training and Test Data')
   (TrainX,TrainY) = lstm.transformData(trainX,trainY,worddict)

   '''
   print('********************** Training Data *********************')
   for i in xrange(0,len(TrainX)):
       print(TrainX[i] , '  :  :  ' , TrainY[i])
   
   print('-------------------------')
   print('Training Data : Input')
   for i in TrainX:
     print(len(i))
   
   print('--------------------------')
   print('Training data : Output')
   for i in TrainY:
     print(len(i)) 
   '''

   (TestX,TestY) = lstm.transformData(testX,testY,worddict)
   
   ''' 
   print('********************** Testing Data **********************')
   for i in xrange(0,len(TestX)):
       print(len(TestX[i]) , '  :  :  ' , TestY[i])   
   
   '''
   TrainX = numpy.array(TrainX)
   TrainY = numpy.array(TrainY)
   TrainY = TrainY.reshape(TrainY.shape[0],1)
   
   print('************* After Numpy transformation *****************')
   #print(TrainX)
   print(TrainX.shape)
   print('--------------------------------')
   #print(TrainY)
   print(TrainY.shape)

   validX, validY = lstm.getValidationData(TrainX,TrainY)

   lstm.configureLSTMModel(TrainX,TrainY,validX,validY)

   
   TestX = numpy.array(TestX)
   TestY = numpy.array(TestY)
   TestY = TestY.reshape(TestY.shape[0],1)
   
   
   print('************* After Numpy transformation *****************')
   #print(TestX)
   print(TestX.shape)
   print('--------------------------------')
   #print(TestY)
   print(TestY.shape)
   
   lstm.predictSentiment(TestX,TestY)
   print('Evaluating the Model')
   lstm.evaluateLSTMModel(TestX,TestY)
   
   
if __name__ =='__main__':
   main()
