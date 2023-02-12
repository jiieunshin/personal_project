#  
rm(list=ls())
#
#
#
#  Read in the data 
dat<- read.csv("C:/Users/jieun/Desktop/hyesang/hw3_hour.csv")
str(dat)
names(dat)

# install.packages("caTools")
library(caTools)
library(dplyr)
# The goal is to predict the total number of rentals each hour, “cnt”.

#Q1. 
str(dat)  # 데이터 탐색
head(dat)

# factor형으로 바꾸기
mnth <- as.factor(dat$mnth)
season <- as.factor(dat$season)
hr <- as.factor(dat$hr)
wkday <- as.factor(dat$wkday)
weathersit <- as.factor(dat$weathersit)

# 더미변수화
tmp_mnth <- data.frame(model.matrix(~mnth-1))
tmp_season <- data.frame(model.matrix(~season-1))
tmp_hr <- data.frame(model.matrix(~hr-1))
tmp_wkday <- data.frame(model.matrix(~wkday-1))
tmp_weathersit <- data.frame(model.matrix(~weathersit-1))

# 필요한 변수만 다시 넣어서 dat1로 만듬
dat1 <- cbind(dat[,c(15,4)], tmp_season[,1:3], 
              tmp_mnth[,1:11], dat[,c(9, 7)], 
              tmp_wkday[,2:5], tmp_hr[,1:23], 
              tmp_weathersit[,2:4], dat[,11:14])
rm(mnth, season, hr, wkday, weathersit)
rm(tmp_mnth, tmp_season, tmp_hr, tmp_wkday, tmp_weathersit)

str(dat1)

#Once the data set is created, run a quick “all-in” regression 
#to identify if there are any linear dependencies between the newly created 
#independent variables.  

reg.all <- lm(cnt ~ ., data=dat1)
summary(reg.all)

# wkday5가 NA로 뜸 -> 종속성이 있다. 변수 1개를 더 제외하자.

#...............................................................................

#Q2.

#Randomly select approximately 50% of the rows for a training data set 
#and include the rest of the data in a test data set.  

set.seed(92407226)
split = sample.split(dat1$cnt, SplitRatio = 0.5)
training = subset(dat1, split == TRUE)
test = subset(dat1, split == FALSE)
as.numeric(dat1$season)

#Run the “all-variables-in” regression model to predict the count of bikes rented 
#on the training data. 
model_training = lm(cnt ~ ., data=training)
summary(model_training)

# training set에서 예측한 자전거 수
fitted_y = model_training$fitted.values %>% as.vector
plot(training$cnt, fitted_y, cex=0.2)

# RMSE를 구하는 방법
# y-y_hat의 제곱합 / n
RMSE_train = sqrt(sum((model_training$fitted.values-training$cnt)^2)/nrow(training))  # test RMSE와 동일 104.5806
sum((y-y_hat)^2)

# 여기서 model_training$fitted.values-training$cnt은
# model_training$residuals와 동일한 값

#...............................................................................

#Q3.
#What is the fit for this model on the training data?  
#What is the fit for the model on the test data?  
#How do they compare?

#compute sigma of the training data: 104.8985
sum.model_training = summary(model_training)
sum.model_training$sigma #104.8985

#compute the RMSE for the test data predictions 
model_test <- predict(model_training, test)       # y hat of test set
summary(model_test)

MSE_test = sum((model_test-test$cnt)^2)/nrow(test)  # RMSE of test set  99.00312
RMSE_test <- sqrt(MSE_test)

RMSE_train
RMSE_test

# RMSE_test #120.7079
# 
# RMSE_train <- sqrt(MSE_train)
# RMSE_train #114.6006

#...............................................................................

#Q4.Find your preferred regression model to predict the count of bikes rented 
#using the training data.  Keep in mind the principles discussed in class:  
#R-squared as high as possible, significant variables, expediency, and most 
#importantly, contextual understanding.   Argue why it is best.  Estimate the RMSE 
#on the test data using this model.  Call this the “best” model. 

library(leaps)
# best model을 정하는데 forward selection을 사용함
regfit.fwd = regsubsets(cnt ~.,data=training, nvmax = 52,
                         method = "forward")

summary(regfit.fwd)$adjr2 %>% plot(.)                 ############ 조정된 R-square, forward selection
summ=summary(regfit.fwd)
summ$rsq %>% plot

# best model은 20번째로 선택한다. adjr2이나 rss가 거의 움직이지 않는 값으로
adjr2 = summary(regfit.fwd)$adjr2

best_id = min(which((adjr2 - lag(adjr2))/adjr2 <= 0.1))   # 혹은 0.01
summary(regfit.fwd)$which[10,]
coef_select = coef(regfit.fwd, 10)  # 회귀계수

# test set 구성
select_model = summary(regfit.fwd)$which[best_id,]
names = names(select_model)[select_model][-1]
dat1_fwd_test = test[,c("cnt",names)]              ### training에서 학습 -> 유의한 변수들로  test set 구성

# test mse 구하기
dat1_fwd_test_mat = model.matrix(cnt~., data = dat1_fwd_test)
yhat_full = dat1_fwd_test_mat[,names(coef_select)] %*% coef_select
MSE_full = mean((dat1_fwd_test$cnt - yhat_full)^2)
RMSE_full = MSE_full^0.5
RMSE_full  # RMSE: 99.09291


# coef(regfit.fwd, 5) #hr9, hr18, hr19, atemp, windspeed
#intercept(-51.79821), hr9(53.32253), hr18(248.02696),
#hr19(119.63707), atemp(418.29539), windspeed(145.98756)

#.........................................................

#5.Using the “best” model from the previous question run LOO, 5-Fold and 
#10-Fold cross-validation.  Save the MSEs and RMSEs for later. 
#What was learned in this question?
library(caret)
select_model = summary(regfit.fwd)$which[best_id,]
names = names(select_model)[select_model][-1]
dat1_fwd = dat1[,c("cnt",names)]

## cross validation은 train, test를 나누지 않음
# LOOCV
ctrl_loocv = trainControl(method = "LOOCV")
model_loocv = train(cnt~., data = dat1_fwd, method = "lm", trControl = ctrl_loocv)  # RMSE: 107.7184
model_loocv$finalModel
model_loocv$resample
MSE_loocv = model_loocv$results$RMSE

# K-fold CV
ctrl_cv5 = trainControl(method = "cv", number = 5)
model_cv5 = train(cnt~., data = dat1_fwd, method = "lm", trControl = ctrl_cv5) # RMSE: 107.7058
print(model_cv5)
model_cv5$finalModel
model_cv5$resample
MSE_cv5 = model_cv5$results$RMSE

# K-fold CV
ctrl_cv10 = trainControl(method = "cv", number = 10)
model_cv10 = train(cnt~., data = dat1_fwd, method = "lm", trControl = ctrl_cv10) # RMSE: 107.7244
print(model_cv10)
model_cv10$finalModel
model_cv10$resample
MSE_cv10 = model_cv10$results$RMSE

MSE_loocv
MSE_cv5
MSE_cv10

#.........................................................
# 6. regfit.full에서 best model 찾기
regfit.full = regsubsets(cnt ~., training, really.big = T)    # really.big = T 추가해줌
summary(regfit.full)

plot(summary(regfit.full)$adjr2)   ############ 조정된 R-square, exhaustive subset selection regression


# forward와 마찬가지로 best model은 20번째로 선택한다. adjr2이나 rss가 거의 움직이지 않는 값으로
adjr2 = summary(regfit.full)$adjr2
plot(adjr2)
best_id = which.min((adjr2 - lag(adjr2))/adjr2)
summary(regfit.full)$which[8,] # 9개의 변수
coef_select = coef(regfit.full, best_id)  # 회귀계수

# test set 구성하기
select_model = summary(regfit.full)$which[best_id,]
names = names(select_model)[select_model][-1]
dat1_test = test[,c("cnt",names)]              ### training에서 학습 -> 유의한 변수들로  test set 구성

# test RMSE 계산하기
dat1_test_mat = model.matrix(cnt~., data = dat1_test)
yhat_full = dat1_test_mat[,names(coef_select)] %*% coef_select
MSE_full = mean((dat1_test$cnt - yhat_full)^2)
RMSE_full = MSE_full^0.5
RMSE_full  # RMSE: 124.8186                


#.........................................................
# 7. stepwise에서 best model 찾기 (forward stepwise와 backward stepwise 비교)

max_lm = formula(lm(cnt~., training))

# forward stepwise
fwd_selection = step(lm(cnt~1, training), direction = "forward", scope = max_lm)
MSE_fwd = sqrt(sum((fwd_selection$residuals)^2)/nrow(training))   # 104.6118


# test set 구성하기
coef = fwd_selection$coefficients
names = names(coef)[-1]
dat1_test = test[,c("cnt",names)]              ### training에서 학습 -> 유의한 변수들로  test set 구성

# test RMSE 계산하기
dat1_test_mat = model.matrix(cnt~., data = dat1_test)
yhat_full = dat1_test_mat[,names(coef)] %*% coef
MSE_full = mean((dat1_test$cnt - yhat_full)^2)
RMSE_full = MSE_full^0.5
RMSE_full  # RMSE: 98.95414    

# backward stepwise
bwd_selection = step(lm(cnt~., training), direction = "backward")
MSE_bwd = sqrt(sum((bwd_selection$residuals)^2)/nrow(training))   # 104.6118

# test set 구성하기
coef = bwd_selection$coefficients
names = names(coef)[-1]
dat1_test = test[,c("cnt",names)]              ### training에서 학습 -> 유의한 변수들로  test set 구성

# test RMSE 계산하기
dat1_test_mat = model.matrix(cnt~., data = dat1_test)
yhat_full = dat1_test_mat[,names(coef)] %*% coef
MSE_full = mean((dat1_test$cnt - yhat_full)^2)
RMSE_full = MSE_full^0.5
RMSE_full  # RMSE: 98.93397    


# 두 모형이 똑같게 선택됨을 알 수 있음.


#.........................................................
# 8. Ridge regression
library(glmnet)
lambdas = seq(0, 2, by = .005)
cv_fit = cv.glmnet(data.matrix(training[,-1]), training[,1], alpha = 0, lambda = lambdas)  # alpha =0 이면 ridge

plot(cv_fit) # MSE plot

opt_lambda = cv_fit$lambda.min
opt_lambda # test set이 시행할때마다 바뀔수 있어 값이 바뀐다.

ridge_fit = glmnet(as.matrix(training[,-1]), training[,1], alpha=0, lambda = opt_lambda)
coef(ridge_fit)  # ridge모형으로부터 얻은 회귀계수

# RMSE 계산하기
y_hat = predict(ridge_fit, s = opt_lambda, newx = as.matrix(test[,-1])) # test data의 y_hat

MSE_ridge = mean((test$cnt - y_hat)^2)
RMSE_ridge = MSE_ridge^0.5
RMSE_ridge  # test RMSE: 98.98959

#.........................................................
# 9. Lasso regression
cv_fit = cv.glmnet(data.matrix(training[,-1]), training[,1], alpha = 1, lambda = lambdas)  # alpha =1 이면 lasso
plot(cv_fit) # MSE plot

opt_lambda = cv_fit$lambda.min
opt_lambda # test set이 시행할때마다 바뀔수 있어 값이 바뀐다.

lasso_fit = glmnet(as.matrix(training[,-1]), training[,1], alpha=1, lambda = opt_lambda)
coef(lasso_fit)  # ridge모형으로부터 얻은 회귀계수

# RMSE 계산하기
y_hat = predict(lasso_fit, s = opt_lambda, newx = as.matrix(test[,-1]))

MSE_lasso = mean((test$cnt - y_hat)^2)
RMSE_lasso = MSE_lasso^0.5
RMSE_lasso  # test RMSE: 98.97462

#.........................................................
# 10. test MSE 비교
# 모든 변수
RMSE_test  # 일반 regression

# 변수선택 후 (cv mse와 test mse)
MSE_loocv  # leave-one-out cv 
MSE_cv5    # 5 fold cross-validation 
MSE_cv10   # 10 fold cross-validation 

RMSE_full  # regfit.full에서 best model
MSE_fwd    # forward stepwise
MSE_bwd    # forward stepwise

# ridge와 lasso
RMSE_ridge # ridge regression
RMSE_lasso # lasso regression

#.........................................................
# 10. 분석 시 중요한 점
# 모형을 잘 선정하자.
# 변수를 선정하는 여러가지 방법을 잘 알고 사용하자.
# 평가지표를 잘 활용하자.

