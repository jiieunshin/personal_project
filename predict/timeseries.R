
rm(list=ls())
library(fpp3)
library(dplyr)
library(forecast)

# Q1. 선형회귀에 유용하도록 데이터클리닝과 변환하기. 
#
#  Read in and set up the data set
#
data = read.csv("C:/Users/jieun/Desktop/hyesang/hw4_home_starts.csv")

####################
# 질적변수를 요일으로 변환
data$Date_factor = as.factor(data$Date)
data$Month_factor = as.factor(data$Month)
data$quarter_factor = as.factor(data$Quarter)

# tslm에서 "시간"을 안널고 단순 회귀분석처럼 돌리면 일반 lm이랑 똑같아요


####################
# 1. 선형회귀를 fitting 해보자.
data$timetr = 1:nrow(data)     # 추세변수 추가
data$timetrsq = data$timetr^2  # 2ck 추세변수 추가
# str(data$Date)

plot(data$timetr, data$Starts, cex=0.5, pch=16, type='l')  # 여기서 선형 회귀선을 그려보자. 반응변수: data$Starts, 독립변수: 날짜

lm_fit1 = lm(data$Starts ~ data$timetr)  # Starts ~ timetr   #### 시간 추세변수
summary(lm_fit1)
summary(lm_fit1)$sigma  # RMSE 36.61693
abline(a = lm_fit1$coefficients[1], b = lm_fit1$coefficients[2], col="red") # a는 절편, b는 기울기

lm_fit2 = lm(data$Starts ~ data$timetr + data$timetrsq)  # Starts ~ timetr + timetr2   #### 시간 추세변수
summary(lm_fit2)
summary(lm_fit2)$sigma # RMSE 36.09246


##########
## 참고 ##
##########
# 질적 변수를 요인으로 바꿈? (모든 날짜를 독립변수로)
#lm_fit = lm(data$Starts ~ as.factor(data$Date)) # 독립변수가 데이터 갯수만큼 나와서 유용한 방법은 아님.
#summary(lm_fit)

# month를 독립변수로?
lm_fit = lm(data$Starts ~ data$Month_factor) # 독립변수가 데이터 갯수만큼 나와서 유용한 방법은 아님.
summary(lm_fit)

# year를 독립변수로?
lm_fit = lm(data$Starts ~ as.factor(data$quarter_factor)) # 독립변수가 데이터 갯수만큼 나와서 유용한 방법은 아님.
summary(lm_fit)

# month, year를 모두 독립변수로
lm_fit = lm(data$Starts ~ as.factor(data$quarter_factor) + as.factor(data$Month_factor)) # 독립변수가 데이터 갯수만큼 나와서 유용한 방법은 아님.
summary(lm_fit)

# 2. 계절변수의 후보 변수: month
plot(data$timetr, data$Starts, cex=0.5, pch=16)  # 요일이 더 잘 드러나게 -> 계절변수는 month가 적절해보임

#.............................................
# Q2. 회귀모형
par(mfrow = c(1,1))  # 그래프 그리기
plot(data$timetr, data$Starts, cex=0.5, pch=16, type='l', main = "before adding season")  # 여기서 선형 회귀선을 그려보자. 반응변수: data$Starts, 독립변수: 날짜

ts_data = ts(data$Starts, frequency = 12, start=c(1959, 1)) # month를 계절변수로 하므로 freq=12, 시작값은 첫 번째 관측값의 year

# timetr의 고차항 추가하기
data$time3 = data$timetr^3
lm_fit3 = tslm(ts_data ~ timetr + timetrsq + time3, data = data) # 3차추세 추가 -> 모두 유의하게 나옴
summary(lm_fit3)
points(data$timetr, lm_fit3$fitted.values, type = 'l', col="pink")

data$time4 = data$timetr^4
lm_fit4 = tslm(ts_data ~ timetr + timetrsq + time3 + time4, data = data) # 4차추세 추가 -> 모두 유의하게 나옴
summary(lm_fit4)
points(data$timetr, lm_fit4$fitted.values, type = 'l', col="green")

# 결과: 고차항을 추가할 때마다 전체적인 추세가 반영되고 있다. (미세하긴 함..)

# 2. 2차 추세모형에 대한 RMSE
RMSE_fit1 = sqrt(sum((lm_fit1$fitted.values-data$Starts)^2)/nrow(data)) # 36.64052
RMSE_fit2 = sqrt(sum((lm_fit2$fitted.values-data$Starts)^2)/nrow(data)) # 36.02095
RMSE_fit3 = sqrt(sum((lm_fit3$fitted.values-data$Starts)^2)/nrow(data)) # 35.73431
RMSE_fit4 = sqrt(sum((lm_fit4$fitted.values-data$Starts)^2)/nrow(data)) # 35.61652
cbind(RMSE_fit1, RMSE_fit2, RMSE_fit3, RMSE_fit4)

#.............................................
# Q3. 위의 2차 추세 모형에 "계절" 변수를 추가한 회귀모형 적합
plot(data$timetr, data$Starts, cex=0.5, pch=16, type='l', main = "after adding season")  # 여기서 선형 회귀선을 그려보자. 반응변수: data$Starts, 독립변수: 날짜

ts3_fit = tslm(ts_data ~ timetr + timetrsq + season, data = data)     # season 추가!!
summary(ts3_fit)
points(data$timetr, ts3_fit$fitted.values, type = 'l', col="red")

RMSE_add_season = sqrt(sum((ts3_fit$fitted.values-data$Starts)^2)/nrow(data)) # 30.80775


#.............................................
# Q4. 위의 2차 추세 모형에 "month" 변수를 추가한 회귀모형 적합

ts4_fit = tslm(ts_data ~ timetr + timetrsq + season + Month, data = data)
ts4_fit = tslm(ts_data ~ timetr + timetrsq + season + Month_factor, data = data)
summary(ts4_fit)  # NA가 뜸.. -> 이미 season이 month이기 때문에 같은 변수이므로 다중공선성!

points(data$timetr, ts4_fit$fitted.values, type = 'l', col="pink")

sqrt(sum((ts4_fit$fitted.values-data$Starts)^2)/nrow(data)) # 30.80775    # 3번문제와 똑같다.


#.............................................
# Q5. 자기상관 체크
###
###
data$Date_format <- as.Date(data$Date, '%m/%d/%Y')
data1 <- mutate(data, YearMonth = yearmonth(Date_format))  # YearMonth라는 변수 생성 (연, 월로 이루어짐)
HSdat <- as_tsibble(data1[,c("Starts", "YearMonth")], index = YearMonth)  # Month와 Starts만 변수로 넣음
str(HSdat)
###
###

autoplot(HSdat)
plot(lag(HSdat$Starts, 1), cex=0.5)   # 1차 차분
plot(lag(HSdat$Starts, 12), cex=0.5)  # 12차 차분

# 차분한 그래프에서 추세가 보이면 자기상관이 있다고 할 수 있음
# 추세가 그대로 존재하고 계절성도 여전히 존재하므로 자기상관이 있다고 할 수 있다.


#.............................................
# Q6. 랜덤워크로 5년 데이터를 생성하고 SNAIVE로 예측 -> RMSE
# naive 예측: 주어진 기간에 대한 예측이 이전 기간에서 관찰된 값과 동일하게 예측.

###########################
##  random walk example  ##
# RW = arima.sim(model = list(order = c(0, 1, 0)), n = 60)  # 5년도 데이터 생성. 랜덤워크는 ARIMA(0,1,0)와 같음
# plot.ts(RW,main = "Random Walk")
###########################


# 1. 데이터 생성: drift가 있는 랜덤워크
diff_dat = diff(data$Starts)[(756-11):755] # 맨 마지막 데이터 12개
RW_drift = arima.sim(model = list(order = c(0, 1, 0)), n = 60, mean = diff_dat, sd = sqrt(sd(diff_dat)))  # 5년도 데이터 생성. 랜덤워크는 ARIMA(0,1,0)와 같음
RW_drift = RW_drift + mean(data$Starts[(756-11):756])

plot.ts(c(data$Starts,RW_drift), main = "Random Walk")
points((817-60):817, RW_drift, col = "red", type='l')   # 추가된 부분
###########################

# 1. 예측하기
# SNAIVE로 예측하기
rwf_hat = rwf(HSdat$Starts, h=60, drift=TRUE)
plot(rwf_hat)
accuracy(rwf_hat)

# SNAIVE로 예측하기
snaive_hat = snaive(HSdat$Starts, h=60)
plot(snaive_hat)
accuracy(snaive_hat)


#.............................................
# Q7. 5-period 이동평균모형 (MA5) 적합 -> RMSE
#############
## example ##
#############
M = 5
dat_len = length(data$Starts)
len = dat_len - M  # 763

Ma = ma(data$Starts, M)     # 이동평균
y_ma_hat = Ma[!is.na(Ma)]     # 한 시점 후의 예측값 구하기 -> 1개가 더 많아서 마지막 1개를 더 빼주어야 함
y_ma_hat = y_ma_hat[-1]       # 763개

residual = data$Starts[(M+1):dat_len] - y_ma_hat  # 원래 값을 M+1번쨰부터 끝까지 맞춰주기. 총 763개
RMSE_MA = sqrt(mean(residual^2)) # RMSE
RMSE_MA

#############
## M값을 다양하게 주기 . 반복문을 활용

par(mfrow=c(1,1))
plot(data$timetr, data$Starts, cex=0.5, pch=16, type='l', main = "MA", lwd=2)  # 여기서 선형 회귀선을 그려보자. 반응변수: data$Starts, 독립변수: 날짜

M = seq(1, 29, 2)
colr = rainbow(length(M))
RMSE_MA = c()
for(m in 1:length(M)){
  cat("calculate MA", M[m], "\n")
  dat_len = length(data$Starts)
  len = dat_len - M[m]  # 763
  
  Ma = ma(data$Starts, M[m])     # 이동평균
  y_ma_hat = Ma[!is.na(Ma)]        # 한 시점 후의 예측값 구하기 -> 1개가 더 많아서 마지막 1개를 더 빼주어야 함
  y_ma_hat = y_ma_hat[-1]       
  
  residual = data$Starts[(M[m]+1):dat_len] - y_ma_hat  
  RMSE_MA[m] = sqrt(mean(residual^2)) # RMSE
  
  points(data$timetr[(M[m]+1):dat_len], y_ma_hat, type = 'l', col = colr[m], lwd = 2)
}

legend("topright", legend = paste0("M=", M), col = colr, lwd = 2)


#.............................................
# Q8. 두 가지 분해, additive, multiplicative 적합 -> random에서 RMSE 계산하기
add_fit = decompose(ts_data, type="additive") 
autoplot(add_fit)

multip_fit = decompose(ts_data, type="multiplicative")   # seasonal의 y limit 범위가 매우 좁아짐
autoplot(multip_fit)

# MSE 계산
add_fit$random
multip_fit$random

not_NA_id = which(!is.na(add_fit$random))

RMSE_add = sqrt(mean((add_fit$random[not_NA_id])^2))   # 10.37575
RMSE_multip = sqrt(mean((multip_fit$random[not_NA_id])^2))  # 1.001707

RMSE_add 
RMSE_multip

#.............................................
# Q9. STL 분해 -> reminder에서 RMSE 계산하기

decomp_STL = stl(ts_data, s.window = 12, t.window = 13, robust = TRUE) # seasonal window=12, trend window=13
autoplot(decomp_STL)

seasonal_stl = decomp_STL$time.series[,1]
trend_stl = decomp_STL$time.series[,2]
reminder_stl = decomp_STL$time.series[,3]

RMSE_stl = sqrt(mean((reminder_stl)^2))  # 8.451222


#.............................................
# Q10. STL 분해 -> reminder에서 RMSE 계산하기

# 선형회귀 적합
RMSE_fit1        # 계절추가 X
RMSE_fit2
RMSE_fit3
RMSE_fit4

RMSE_add_season  # 계절 추가


RMSE_MA  # 이동평균법


# 분해법
RMSE_add 
RMSE_multip

RMSE_stl

# 계절성이 반영해야 RMSE가 작아진다.
# 분해법의 RMSE 중 multiplication 분해 방법이 가장 RMSE가 작았다.



