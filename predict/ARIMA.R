
rm(list=ls())
library(fpp3)
library(dplyr)


# Q1. 다음 조건에 맞는 시계열 데이터를 생성하고 ACF, PACF를 비교해보기
library(forecast)

# a.	White noise
noise = rnorm(200)

# b.	AR(1) with parameter, 1 = 0.6
sim_b = arima.sim(list(ar=c(0.6)), n=200, innov=noise)

# c.	AR(2) with parameters, 1 = 0.6 and 2 = 0.3
sim_c = arima.sim(list(ar=c(0.6, 0.3)), n=200, innov=noise)

# d.	AR(2) with parameters, 1 = 0.8 and 2 = – 0.3
sim_d = arima.sim(list(ar=c(0.8, -0.3)), n=200, innov=noise)

# e.	MA(1) with parameter, 1 = 0.6
sim_e = arima.sim(list(ma=c(0.6)), n=200, innov=noise)

# f.	ARMA(1,1) with parameters, 1 = 0.5 and 1 = 0.4
sim_f = arima.sim(list(ar=c(0.5), ma=c(0.4)), n=200, innov=noise)

# g.	ARIMA(1,1,1) with parameters, 1 = 0.5 and 1 = 0.4
sim_g = arima.sim(list(order = c(1,1,1), ar=c(0.5), ma=c(0.4)), n=200, innov=noise)

# h.	ARIMA(1,1,1)(0,1,0)[4] with parameters, 1 = 0.5 and 1 = 0.4
model_h = Arima(ts(noise,freq=4), order=c(1,1,1), seasonal=c(0,1,0),
                fixed=c(phi=0.5, theta=0.4))
sim_h = simulate(model_h, nsim=200)

# 시각적으로 비교 : 데이터, ACF, PACF
par(mfrow=c(3,8))
ts.plot(noise, main = "noise")
ts.plot(sim_b, main = "AR(1) with 0.6")
ts.plot(sim_c, main = "AR(2) with (0.6, 0.3)")
ts.plot(sim_d, main = "AR(2) with (0.8, -0.3)")
ts.plot(sim_e, main = "MA(1) with 0.6")
ts.plot(sim_f, main = "ARMA(1,1) with 0.5 and 0.4")
ts.plot(sim_g, main = "ARIMA(1,1,1) with 0.5 and 0.4")
ts.plot(sim_h, main = "ARIMA(1,1,1)(0,1,0)[4] with 0.5 and 0.4")

acf(noise, main = "noise")
acf(sim_b, main = "AR(1) with 0.6")
acf(sim_c, main = "AR(2) with (0.6, 0.3)")
acf(sim_d, main = "AR(2) with (0.8, -0.3)")
acf(sim_e, main = "MA(1) with 0.6")
acf(sim_f, main = "ARMA(1,1) with 0.5 and 0.4")
acf(sim_g, main = "ARIMA(1,1,1) with 0.5 and 0.4")
acf(sim_h, main = "ARIMA(1,1,1)(0,1,0)[4] with 0.5 and 0.4")
# x축은 시차(lag), y축은 autocorrelation
# 시차가 0일 때, autocorrelation은 항상 1의 값을 가진다.
# 대부분 값들이 파란선 내부에 위치한 것으로 보아 정상성을 가짐을 유추할 수 있다.

pacf(noise, main = "noise")
pacf(sim_b, main = "AR(1) with 0.6")
pacf(sim_c, main = "AR(2) with (0.6, 0.3)")
pacf(sim_d, main = "AR(2) with (0.8, -0.3)")
pacf(sim_e, main = "MA(1) with 0.6")
pacf(sim_f, main = "ARMA(1,1) with 0.5 and 0.4")
pacf(sim_g, main = "ARIMA(1,1,1) with 0.5 and 0.4")
pacf(sim_h, main = "ARIMA(1,1,1)(0,1,0)[4] with 0.5 and 0.4")
# x축은 시차(lag), y축은 partial autocorrelation
par(mfrow=c(1,1))


# Q2. 데이터 불러오기

data = read.csv("C:/Users/jieun/Desktop/hyesang/week6/hw6_USGDP.csv")
head(data)

# a. ts 데이터 형식으로 바꾸기
data$Date <- as.Date(data$Date)
datts <- ts(data$USGDP, start = 1947, frequency = 4)  # 주기가 4 이므로
GDPts <- as_tsibble(datts)
names(GDPts)[2] <- "GDP"
names(GDPts)

autoplot(GDPts, GDP) 

# 박스콕스 변환
lambda = pull(features(GDPts, GDP, features = guerrero), lambda_guerrero)
autoplot(GDPts, box_cox(GDP, lambda))                   # 계절성의 분산이 일정하게 됨

# b. 적절한 ARIMA model을 적용하기
fit_boxcox = model(GDPts, 
                   search = ARIMA(box_cox(GDP, lambda)),
                   auto = ARIMA(box_cox(GDP, lambda), stepwise = FALSE, approx = FALSE))
# search: ARIMA(0,1,2)(0,1,2)[4] 모델이 선택됨, RMSE:16915
# auto: ARIMA(4,1,0)(2,1,0)[4] 모델이 선택됨,   RMSE:16575

fabletools::accuracy(fit_boxcox)  

# c. 3가지의 ARIMA 모델을 적용해보기
fit_ARIMA3 = model(GDPts, 
                   fit1 = ARIMA(box_cox(GDP, lambda) ~ pdq(1, 0, 0)),   # ARIMA(1,0,0)(0,1,2)[4]
                   fit2 = ARIMA(box_cox(GDP, lambda) ~ pdq(0, 1, 1)),   # ARIMA(0,1,1)(0,1,2)[4]
                   fit3 = ARIMA(box_cox(GDP, lambda) ~ pdq(1, 1, 1)))   # ARIMA(1,1,1)(0,1,2)[4]

fabletools::accuracy(fit_ARIMA3)  # RMSE: 17383, 17140, 16951

# d. residual diagnostics
gg_tsresiduals(select(fit_boxcox, search))
gg_tsresiduals(select(fit_boxcox, auto))

gg_tsresiduals(select(fit_ARIMA3, fit1))
gg_tsresiduals(select(fit_ARIMA3, fit2))
gg_tsresiduals(select(fit_ARIMA3, fit3))

# e. 향후 5년 예측하기
forc_boxcox = fabletools::forecast(fit_boxcox, h = 20)
autoplot(forc_boxcox, GDPts)

forc_ARIMA3 = fabletools::forecast(fit_ARIMA3, h = 20)
autoplot(forc_ARIMA3, GDPts)

# f. ETS 모형 적합하기
fit_ETS = model(GDPts, ETS(box_cox(GDP, lambda), opt_crit = "mse"))   # ETS(A,A,A) 모형이 선택됨

fabletools::accuracy(fit_ETS)                         # RMSE: 18101
forc_ETS = fabletools::forecast(fit_ETS, h = 20)

autoplot(forc_ETS, GDPts, level = 95, colour = "red") 


# Q3. 미국 1인가족 주택판매 데이터로 위의 과정 반복하기

data2 = read.csv("C:/Users/jieun/Desktop/hyesang/week6/hw6_one_family_homes.csv")
head(data2)

# a. ts 데이터 형식으로 바꾸기
data2$Date <- as.Date(data2$Date, "%m/%d/%Y")
datts2 <- ts(data2$SFH_Sales, start = 1963, frequency = 12)  # 주기가 12 이므로
Salets <- as_tsibble(datts2)
names(Salets)[2] <- "SFH_Sales"
names(Salets)
autoplot(Salets, SFH_Sales) 

# 모델링
lambda2 = pull(features(Salets, SFH_Sales, features = guerrero), lambda_guerrero)
autoplot(Salets, box_cox(SFH_Sales, lambda2))     # 그래프 상에서 큰 차이 없음


# b. 적절한 ARIMA model을 적용하기
fit_boxcox2 = model(Salets, 
                   search = ARIMA(box_cox(SFH_Sales, lambda2)),   # ARIMA(1,1,2)(1,0,2)[12]
                   auto = ARIMA(box_cox(SFH_Sales, lambda2),      # ARIMA(2,1,2)(1,0,1)[12]
                                stepwise = FALSE, approx = FALSE))

fit_ETS2 = model(Salets, ETS(box_cox(SFH_Sales, lambda2), opt_crit = "mse") )   # ETS(M,N,N) 모형이 선택됨


forc_boxcox2 = fabletools::forecast(fit_boxcox2, h = 60)  # 향후 5년 예측
forc_ETS2 = fabletools::forecast(fit_ETS2, h = 60)

fabletools::accuracy(fit_boxcox2)  # RMSE: 44.1(search), 43.9(auto)
fabletools::accuracy(fit_ETS2)     # RMSE: 45.0

autoplot(forc_boxcox2, Salets)
autoplot(forc_ETS2, Salets) 



