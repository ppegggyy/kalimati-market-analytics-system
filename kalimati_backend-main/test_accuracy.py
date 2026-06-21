import pandas as pd
from sqlalchemy import create_engine
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import numpy as np
import warnings
warnings.filterwarnings('ignore')

try:
    engine = create_engine("postgresql://postgres:admin123@localhost:5432/kalimati")
    df_products = pd.read_sql("SELECT product, COUNT(*) FROM prices GROUP BY product ORDER BY COUNT(*) DESC LIMIT 5", engine)
    
    maes, rmses, mapes = [], [], []
    
    for _, row in df_products.iterrows():
        product = row['product']
        df = pd.read_sql(f"SELECT date, avg_price FROM prices WHERE product = '{product}' ORDER BY date", engine)
        df['date'] = pd.to_datetime(df['date'])
        series = df.set_index('date')['avg_price'].asfreq('D').ffill().dropna()
        
        if len(series) > 100:
            train = series.iloc[:-30]
            test = series.iloc[-30:]
            
            try:
                model = ARIMA(train, order=(2,1,1))
                fitted = model.fit()
                predictions = fitted.forecast(steps=30)
                
                mae = mean_absolute_error(test, predictions)
                rmse = np.sqrt(mean_squared_error(test, predictions))
                mape = mean_absolute_percentage_error(test, predictions) * 100
                
                maes.append(mae)
                rmses.append(rmse)
                mapes.append(mape)
            except:
                pass

    print(f"Average MAE: {np.mean(maes):.2f} Rs")
    print(f"Average RMSE: {np.mean(rmses):.2f} Rs")
    print(f"Average MAPE: {np.mean(mapes):.2f}%")
except Exception as e:
    print(f"Error: {e}")
