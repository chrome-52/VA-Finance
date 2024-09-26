from scipy import stats

''' Blanket class for expense prediction with linear regression'''
class ExpensePredictionLinear:
  # Initializer. Data must be two/three-column
  # dataframe with headings 'Date' and 'Amount'
  def __init__(self, slope=0, daily=1):
    self.slope = None
    self.current = None

  # Utility function to get slope of line
  def fit_slope(self, spendings):
    Y = np.array([np.sum(spendings[:i]) for i in range(len(spendings))])
    X = np.array([i for i in range(len(spendings))])
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)
    self.slope = slope
    return

  # Fit function for usage
  def fit(self, data):
    self.current = np.sum(data['Amount'])
    daily_spends = []
    start = 0
    end = 0
    while start < len(data):
      while end < len(data) and (data['Date'][start] == data['Date'][end]):
        end += 1
      daily_spends.append(np.sum((data[start:end])['Amount']))
      start = end
    self.fit_slope(daily_spends)
    return

  # Predict the total expenses after given number of days
  def predict(self, num_days):
    prediction = self.current + num_days*self.slope
    return prediction
#Nothing to see here
