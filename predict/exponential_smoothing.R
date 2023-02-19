
rm(list=ls())
library(fpp3)
library(dplyr)
library(forecast)

# Q1. 선형회귀에 유용하도록 데이터클리닝과 변환하기. 
#
#  Read in and set up the data set
#
data = read.csv("C:/Users/jieun/Desktop/hyesang/hw5_bike_share_day.csv")
head(data)

# 1. ts 데이터 형식으로 바꾸기
data$dteday = as.Date(data$dteday, format = "%m/%d/%Y")  # Date 형식으로 바꾸어 줌.
cnts = ts(data[,14], frequency = 7)   # start: "2011-01-01"
cntts = as_tsibble(cnts)
cntts = mutate(cntts, index = data[,2])
names(cntts)[2] = "count"  # 변수명 변경
str(cntts)

autoplot(cntts, count)     # autoplot: ts 형식을 그래프 그려주는 함수, 삐죽 튀어나온 신호들이 보임
                           # 단순 plot(data$cnt, type='l')과 같음

# 2. 지수평활모형 (ses) 적합, trend와 alpha를 조절!
fit_ses25 = model(cntts, ETS(count ~ error("A") + trend("N", alpha = 0.25) + season("N")))
report(fit_ses25)
fabletools::accuracy(fit_ses25)    # RMSE: 965

fit_ses75 = model(cntts, ETS(count ~ error("A") + trend("N", alpha = 0.75) + season("N")))
report(fit_ses75)
fabletools::accuracy(fit_ses75)    # RMSE: 1006

# 3. naive 모형 적합
fit_naive = model(cntts, Mean = MEAN(count), Naive = NAIVE(count))        # 단순히 mean만 사용해서.

fabletools::accuracy(fit_naive)  # RMSE: 1065
# ses is better.

#.............................................
# Q2. Holt's model (no damping & with damping) 적합하기, trend와 phi를 조절!

fit_Holt = model(cntts, ETS(count ~ error("A") + trend("A") + season("N")) )    # 1. with additive
fit_Holtd = model(cntts, ETS(count ~ error("A") + trend("Ad", phi=0.8) + season("N")) )  # 2. with damped additive trend
                                                                                #    phi = 0.8 (최솟값 권장), trend("Ad", phi = 0.8)으로 변경
# report(fit_Holt)
# report(fit_Holtd)


fabletools::accuracy(fit_Holt)  # Check model accuracy, RMSE: 965
fabletools::accuracy(fit_Holtd)  # Check model accuracy, RMSE: 965

#.............................................
# Q3. Holt's Winters' seasonal model 적합, season과 gamma를 조절!
fit_HWa1 = model(cntts, ETS(count ~ error("A") + trend("A") + season("A")) )    # no damping, phi = 0.98 (default)
fit_HWa2 = model(cntts, ETS(count ~ error("A") + trend("A") + season("M")) )

fit_HWadam1 = model(cntts, ETS(count ~ error("A") + trend("Ad", phi = 0.8) + season("A")) )   # damping, 차이가 잘 안보여 phi=0.8로 명시해줌
fit_HWadam2 = model(cntts, ETS(count ~ error("A") + trend("Ad", phi = 0.8) + season("M")) )

fabletools::accuracy(fit_HWa1)  # Check model accuracy, RMSE: 953
fabletools::accuracy(fit_HWa2)  # Check model accuracy, RMSE: 957
fabletools::accuracy(fit_HWadam1)  # Check model accuracy, RMSE: 952
fabletools::accuracy(fit_HWadam2)  # Check model accuracy, RMSE: 953


#.............................................
# Q4. 위에서 적합한 모형들로 4주간 예측값 생성하기

forc_ses25 = fabletools::forecast(fit_ses25, h = 28)
forc_Holtd = fabletools::forecast(fit_Holtd, h = 28)
forc_HWa1 = fabletools::forecast(fit_HWa1, h = 28)
forc_HWa2 = fabletools::forecast(fit_HWa2, h = 28)
forc_HWadam1 = fabletools::forecast(fit_HWadam1, h = 28)
forc_HWadam2 = fabletools::forecast(fit_HWadam2, h = 28)

#  Plot these
autoplot(forc_ses25, cntts, level = NULL, colour = "red") +
  autolayer(forc_Holtd, cntts, level = NULL, colour = "orange") +
  autolayer(forc_HWa1, cntts, level = NULL, colour = "yellow") +
  autolayer(forc_HWa2, cntts, level = NULL, colour = "green") +
  autolayer(forc_HWadam1, cntts, level = NULL, colour = "blue") +
  autolayer(forc_HWadam2, cntts, level = NULL, colour = "purple") +
  labs(y = "count", title = "Bike sharing", x = "Day")


#.............................................
# Q5. 존슨 앤 존슨 데이터 불러오기

library(fpp3)
data("JohnsonJohnson")  # load the data

JJ = JohnsonJohnson     # 이미 time-series 데이터
str(JohnsonJohnson)
JJts = as_tsibble(JJ, index = yearquarter())
names(JJts)[2] = "QE"
str(JJts)

# JJ데이터는 1960~80년동안 분기별로 측정된 주식 1주당 분기 수익(달러) 데이터로, 총 84개가 측정되었다.
range(JJts$QE)  #  수익의 범위: 0.44 ~ 16.20
autoplot(JJts)

#.............................................
# Q6. JJ 데이터에 ETS모형 적합하기
# 위에서 적합했던 모형들 그대로 사용함

fit_JJHolt = model(JJts, ETS(QE ~ error("A") + trend("A") + season("N")) )                 # with additive
fit_JJHoltd = model(JJts, ETS(QE ~ error("A") + trend("Ad") + season("N")) )               # with damped additive trend
fit_JJses25 = model(JJts, ETS(QE ~ error("A") + trend("N", alpha = 0.25) + season("N")))   # SES model with theta=0.25
fit_JJses75 = model(JJts, ETS(QE ~ error("A") + trend("N", alpha = 0.75) + season("N")))   # SES model with theta=0.75

fit_JJHWa1 = model(JJts, ETS(QE ~ error("A") + trend("A") + season("A")) )       # Holt's Winters' seasonal model (no damping)
fit_JJHWa2 = model(JJts, ETS(QE ~ error("A") + trend("A") + season("M")) )   
fit_JJHWadam1 = model(JJts, ETS(QE ~ error("A") + trend("Ad", phi=0.8) + season("A")) )   # with damping
fit_JJHWadam2 = model(JJts, ETS(QE ~ error("A") + trend("Ad", phi=0.8) + season("M")) )

# accuracy
fabletools::accuracy(fit_JJHolt)  # RMSE: 0.982
fabletools::accuracy(fit_JJHoltd) # RMSE: 0.982
fabletools::accuracy(fit_JJses25) # RMSE: 0.834
fabletools::accuracy(fit_JJses75) # RMSE: 1.26

fabletools::accuracy(fit_JJHWa1)  # RMSE: 0.436
fabletools::accuracy(fit_JJHWa2)  # RMSE: 0.441
fabletools::accuracy(fit_JJHWadam1)  # RMSE: 0.445
fabletools::accuracy(fit_JJHWadam2)  # RMSE: 0.440

# 다음 3년 예측하기(h=4x3=12)

forc_JJHolt = fabletools::forecast(fit_JJHolt, h = 12)
forc_JJHoltd = fabletools::forecast(fit_JJHoltd, h = 12)
forc_JJses25 = fabletools::forecast(fit_JJses25, h = 12)
forc_JJses75 = fabletools::forecast(fit_JJses75, h = 12)

forc_JJHWa1 = fabletools::forecast(fit_JJHWa1, h = 12)
forc_JJHWa2 = fabletools::forecast(fit_JJHWa2, h = 12)
forc_JJHWadam1 = fabletools::forecast(fit_JJHWadam1, h = 12)
forc_JJHWadam2 = fabletools::forecast(fit_JJHWadam2, h = 12)

#  Plot these
autoplot(forc_JJHolt, JJts, level = NULL, colour = "red") +
  autolayer(forc_JJHoltd, JJts, level = NULL, colour = "pink") +
  autolayer(forc_JJses25, JJts, level = NULL, colour = "orange") +
  autolayer(forc_JJses75, JJts, level = NULL, colour = "darkorange") +
  autolayer(forc_JJHWa1, JJts, level = NULL, colour = "yellow") +
  autolayer(forc_JJHWa2, JJts, level = NULL, colour = "green") +
  autolayer(forc_JJHWadam1, JJts, level = NULL, colour = "darkgreen") +
  autolayer(forc_JJHWadam2, JJts, level = NULL, colour = "skyblue") +
  labs(y = "QE", title = "JohnsonJohnson", x = "Quarter")

# Holt's Winters 모형들 are better 


#.............................................
# Q7. 자동적으로 ETS모형 선택하기

fit_JJETS = model(JJts, ETS(QE, opt_crit = "mse") )   # opt_crit 옵션으로 모형선택기준을 줄 수 있음
fabletools::accuracy(fit_JJETS)  # RMSE: 0.471
forc_JJETS = fabletools::forecast(fit_JJETS, h = 12)

#  Plot these
autoplot(forc_JJHolt, JJts, level = NULL, colour = "red") +
  autolayer(forc_JJHoltd, JJts, level = NULL, colour = "pink") +
  autolayer(forc_JJses25, JJts, level = NULL, colour = "orange") +
  autolayer(forc_JJses75, JJts, level = NULL, colour = "darkorange") +
  autolayer(forc_JJHWa1, JJts, level = NULL, colour = "yellow") +
  autolayer(forc_JJHWa2, JJts, level = NULL, colour = "green") +
  autolayer(forc_JJHWadam1, JJts, level = NULL, colour = "darkgreen") +
  autolayer(forc_JJHWadam2, JJts, level = NULL, colour = "skyblue") +
  autolayer(forc_JJETS, JJts, level = NULL, colour = "purple") +       ### 추가됨
  labs(y = "QE", title = "JohnsonJohnson", x = "Quarter")

# ETS에 아무 옵션을 지정하지 않으면 된다.


#.............................................
# Q8. us_employment 데이터

data("us_employment")
usemp = us_employment
usemp = filter(usemp, Title == "Total Private")
usemp = usemp[,c(1,4)]

autoplot(usemp, Employed) 

# modeling
fit_usETS = model(usemp, ETS(Employed, opt_crit = "mse")) # 모형선택기준:mse
fabletools::accuracy(fit_usETS)                           # RMSE: 290
forc_usETS = fabletools::forecast(fit_usETS, h = 60)      # h = 12*5 = 60 (5년 예측)

# Plotting
autoplot(forc_usETS, usemp, level = 80, colour = "red") +
  labs(y = "Employed", title = "US employment", x = "Month")

summary(iris)

#.............................................
# Q9. google closing price 데이터
data("gafa_stock")
goog2015 = filter(gafa_stock, Symbol == "GOOG", year(Date) == 2015)
goog2015 = mutate(goog2015, day = row_number())
goog2015 = update_tsibble(goog2015, index = day, regular = TRUE)  

autoplot(goog2015, Close) 

# modeling
fit_googETS = model(goog2015, ETS(Close, opt_crit = "mse")) # 모형선택기준:mse
fabletools::accuracy(fit_googETS)                           # RMSE: 11.2
forc_googETS = fabletools::forecast(fit_googETS, h = 30)    # h = 30*1 = 60 (30일 예측)

# Plotting
autoplot(forc_googETS, goog2015, level = 80, colour = "red") +
  labs(y = "Close", title = "Google closing price", x = "Day")

#.............................................
# Q10. google closing price데이터에 ARIMA model 적합

fit_goog_ARIMA = model(goog2015, ARIMA(Close))  # ARIMA(0,1,1)
report(fit_goog_ARIMA)

fabletools::accuracy(fit_goog_ARIMA)                           # RMSE: 11.1
forc_goog_ARIMA = fabletools::forecast(fit_goog_ARIMA, h = 30) # h = 30*1 = 60 (30일 예측)

# Plotting
autoplot(forc_googETS, goog2015, level = NULL, colour = "red") +
  autolayer(forc_goog_ARIMA, goog2015, level = NULL, colour = "blue") +
  labs(y = "Close", title = "Google closing price", x = "Day")





