import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler

module_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
model = hub.load(module_url)

''' Blanket class to allow the VA to predict the category 
to which a user query belongs using a similarity metric '''
default_cat_dict = {"Budget Setting":["Set a budget"], \
                    "Expense Logging":["Log an expense", "I just spent rupees"], \
                    "Budget Inquiry":["What is my budget", "How much can I spend", "Show monthly budget"], \
                    "Expense Inquiry":["Show expenses", "How much have I spent", "How much did I spend"], \
                    "Financial Analysis":["Analyze my spending", "Predict my expenses"], \
                    "Market Insights":["What is the stock price", "What is the exchange rate", "Bitcoin price"]}

class SentimentAnalysisSimilarity:
  # Initializer
  def __init__(self, cat_dict=default_cat_dict, mode='operation'):
    self.cat_dict = {j:model(default_cat_dict[j]).numpy() for j in default_cat_dict.keys()}
    self.mode = mode

  # Function to predict average score for each class
  def classify(self, query):
    vec = (model([query]).numpy()).reshape((512,))
    scores = [np.max(np.dot(mat, vec)) for mat in self.cat_dict.values()]
    query_class = list(self.cat_dict.keys())[np.argmax(scores)]
    return query_class


''' Blanket class to allow the VA to predict the category to 
which a user query belongs using a decision tree classifier'''
budget_setting = ['Establish a monthly budget', 'Create a budget plan for the month', "Outline this month's spending limits", 'Plan the budget for the month', \
                  'Allocate funds for this month', 'Determine monthly financial limits', 'Set budget', 'Draft a budget for this month', \
                  'Designate a spending plan for the month', "Organize this month's finances"]

expense_logging = ['Record an expense', 'Track an expense', 'log an expense', 'I invested money in', 'I purchased something', 'I made a purchase', \
                   'I allocated funds', 'I forked out money', 'I paid', 'I incurred an expense']

budget_inquiry = ['Budget inquiry', "What’s my budget at the moment", 'Can you tell me my current budget status', 'What is my available budget', \
                  'How much is left in my budget currently', "What’s left in my budget", "What does my budget look like right now", 'How more can I spend this month', \
                  "What’s my spending limit at the moment", 'Can you give me an overview of my current budget']

expense_inquiry = ['What’s my total spending for this month', 'How much cash have I used so far this month', 'Can you tell me my expenses for the month', \
                   "What’s the total amount I’ve spent this month", 'How much have I incurred in expenses this month', 'Can you provide my monthly spending figure', \
                   "What’s my monthly expenditure so far", 'How much have I allocated this month', 'Can you summarize my spending this month', 'View expenses']

financial_insights = ['Evaluate my financial situation', 'Review my financial standing', 'Assess my financial health', 'Examine my financial condition', \
                      'Give me financial insights', 'Analyze my expenses', 'What recommendations do you have for my finances', 'How can I improve my financial outlook', \
                      'What patterns do you see in my spending', 'Could you highlight any financial opportunities or risks']

class SentimentAnalysisTree:
  # Initializer
  def __init__(self, PCA_dim=4, budget_setting=budget_setting, budget_inquiry=budget_inquiry, \
               expense_logging=expense_logging, expense_inquiry=expense_inquiry, financial_insights=financial_insights):
    self.PCA = None
    self.tree = None
    self.scaler = None
    self.model = model
    self.PCA_dim = PCA_dim
    self.budget_setting = budget_setting
    self.budget_inquiry = budget_inquiry
    self.expense_inquiry = expense_inquiry
    self.expense_logging = expense_logging
    self.financial_insights = financial_insights
    self.built = False
    self.labeldict = {0:'set budget', 1:'log expense', 2:'check budget', 3:'view expenses', 4:'financial analysis'}

  # Fit a decision tree to initialize the classifier, edited at each error instance
  def fit_tree(self):
    mat = model(self.budget_setting + self.expense_logging + self.budget_inquiry \
                + self.expense_inquiry + self.financial_insights).numpy()
    #getting the labels set
    labels = [0 for i in range(len(budget_setting))] + [1 for i in range(len(expense_logging))] + \
             [2 for i in range(len(budget_inquiry))] + [3 for i  in range(len(expense_inquiry))] \
                                                      + [4 for i in range(len(financial_insights))]
    #scaling the data and getting PCA of the training matrix
    scaling = StandardScaler()
    scaling.fit(mat)
    self.scaler = scaling
    scaled_mat = scaling.transform(mat)
    decomp = PCA(n_components=self.PCA_dim)
    decomp.fit(scaled_mat)
    self.PCA = decomp
    #fitting the decision tree
    tree = DecisionTreeClassifier()
    tree.fit(decomp.transform(scaled_mat), labels)
    self.tree = tree
    return

  # In case there was a prediction error, refit the tree with a new set of labelled data
  def refit_tree(self, query, query_class):
    class_dict = {'budget inquiry':self.budget_inquiry, 'budget seeting':self.budget_setting, 'expense logging':self.expense_logging, \
                  'expense inquiry':self.expense_inquiry, 'financial insights':self.financial_insights, 'market insights':None}
    if class_dict[query_class] is None:
      print('Currently, we only support standard commands for market insights. Please be on the lookout for future releases!')
      return
    class_dict[query_class].append(query)
    self.fit_tree()
    return 

  # Predict the query category
  def predict(self, query):
    #if a tree has not been fit, do so
    if not self.built:
      self.fit_tree()
      self.built = True
    #classify the query
    query = self.scaler.transform(self.model([query]))
    label = self.tree.predict(self.PCA.transform(query))
    return(self.labeldict[label[0]])
