
rm(list=ls())
library(dplyr)

# Q1. 데이터 로드 및 크리닝 (appendix 참고)

dat <- read.csv("C:\\Users\\jieun\\Desktop\\hyesang\\week7\\hw7_bank_term_deposit_big.csv")
str(dat)
#
#  Create factor for some variables
#
jb <- as.factor(dat$job)
mari <- as.factor(dat$marital)
ed <- as.factor(dat$education)
cntct <- as.factor(dat$contact)
m <- as.factor(dat$month)
pout <- as.factor(dat$poutcome)
#
#  Convert variables to indicators
#    Note some variables have 2 levels and some have more
#
tmp_job <- data.frame(model.matrix(~jb - 1))
tmp_marit <- data.frame(model.matrix(~mari - 1))
tmp_educ <- data.frame(model.matrix(~ed - 1))
tmp_contact <- data.frame(model.matrix(~cntct - 1))
tmp_month <- data.frame(model.matrix(~m - 1))
tmp_poutcome <- data.frame(model.matrix(~pout - 1))
dat$loan <- as.numeric(as.factor(dat$loan)) - 1
dat$default <- as.numeric(as.factor(dat$default)) - 1
dat$housing <- as.numeric(as.factor(dat$housing)) - 1
dat$deposit <- as.numeric(as.factor(dat$deposit)) - 1
#
#  Take care of “pdays”
#
pdaysnew <- ifelse(dat$pdays != -1, dat$pdays, 0)
#
#  Bind stuff together in a new data frame
#
names(dat)
dat1 <- cbind(dat[,c(17,1,5:8,10,12:13,15)],
              tmp_job[,1:11], tmp_marit[,1:2], tmp_educ[,1:3],
              tmp_contact[,1:2], tmp_month[,1:11], 
              tmp_poutcome[,1:3],
              data.frame(pdaysnew))
names(dat1)
#
#  Get rid of junk for simplicity
#
rm(tmp_job, tmp_marit, tmp_contact,
   tmp_month, tmp_poutcome, tmp_educ)
rm(jb, mari, ed, cntct, m, pout, pdaysnew)

## 
head(dat1)  

# 종속변수: deposit -> 분류하는 것이 목적.
# pdays는 -1~871의 값 -> pdaysnew 0~871까지의 값으로 바꿈
# 데이터의 변환은 범주형 변수로 분석할 변수 (job, matrit, deuc, contact, month, poutcome)는 factor형식으로 바꾸었다. 
# 그 중 다시 범주형이 아니라 연속형으로 분석할 변수 (loan, default, housing, deposit)는 numeric으로 바꿔주었다.


# Q2. 상관관계 계산
cor_mat = cor(dat1)
cor_deposit = cor_mat[-1,1]   # deposit과 다른 변수들 간 상관관계만 추출, deposit 값은 제외
names(cor_deposit) = colnames(cor_mat)[-1]  # 이름 지정
cor_deposit = sort(cor_deposit, decreasing = T)  # 내림차순 정렬

bp_top = barplot(cor_deposit[1:10], main = "상위10개의 상관계수")
text(bp_top, cor_deposit[1:10]-0.05, label = round(cor_deposit[1:10], 4))

# deposit 가장 연관되어있는 세 변수는 age, default, balance.
# deposit이 연속형 변수는 아니기 때문에 상관계수가 완벽한 방법은 아니지만 탐색용으로는 가능하다.

# training set으로 사용할 각 2000명 추출
dep0_id = which(dat1$deposit == 0)   # 39922
dep1_id = which(dat1$deposit == 1)   # 5289

train0_id = sort(sample(dep0_id, 2000))     ## 여기서 sub sample이 어떻게 뽑히느냐에 따라서 밑에 결과들이 달라짐!!
train1_id = sort(sample(dep1_id, 2000))
train = dat1[c(train0_id, train1_id),]
train$deposit %>% table  # 2000:2000

# 나머지 데이터 중 50:50으로 분할
test = dat1[-c(train0_id, train1_id),]
test$deposit %>% table  # 37922 3289

test_dep0_id = which(test$deposit == 0)
test_dep0_id = sample(test_dep0_id, 3289)
test_dep1_id = which(test$deposit == 1)

test = test[c(test_dep0_id, test_dep1_id),]
dim(test)  # 6578 43
test$deposit %>% table  # 3289 3289


# Q3. 로지스틱 회귀모형 적합
logit_fit = glm(deposit~., data = train, family = "binomial")
summary(logit_fit)

# 유의한 변수: 
# balance, housing, loan, duration, campaign, marimarried, 
# cntctcellular, cntcttelephone, mapr, maug, mfeb, mjan, mjul, mjun, mmay, mnov, 
# poutsuccess


# test 데이터에 적합시키기
test_yhat1 = predict(logit_fit, test, type = "response")
test_yhat1 = ifelse(test_yhat1 < 0.5, 0, 1)

tb1 = table(test$deposit, test_yhat1)
rownames(tb1) = c("true0", "true1")
colnames(tb1) = c("pred0", "pred1")
tb1
# accuracy = (2719+2686)/6578 = 0.822


# Q4. 변수선택 후 로지스틱

library(MASS)
stepwise_logit = glm(deposit~., data = train, family = "binomial") %>% stepAIC(trace = FALSE)
summary(stepwise_logit)  # 선택된 변수들만 나타남

test_yhat2 = predict(stepwise_logit, test, type = "response")
test_yhat2 = ifelse(test_yhat2 < 0.5, 0, 1)

tb2 = table(test$deposit, test_yhat2)
rownames(tb2) = c("true0", "true1")
colnames(tb2) = c("pred0", "pred1")
tb2
# accuracy = (2733+2686)/6578 = 0.824

# Q5. 선택된 변수로만 구성함 -> 선형판별
sub_coef = names(stepwise_logit$coefficients)[-1]
train_sub = train[,c("deposit", sub_coef)]
test_sub = test[,c("deposit", sub_coef)]

lda_fit = lda(deposit~., data = train_sub)
lda_fit

lda_pred = predict(lda_fit, test_sub)
lda_pred$posterior  # 사후확률
test_yhat3 = lda_pred$class  # 추정된 class

tb3 = table(test$deposit, test_yhat3)
rownames(tb3) = c("true0", "true1")
colnames(tb3) = c("pred0", "pred1")
tb3
# accuracy = (2787+2605)/6578 = 0.820


# Q6. 나이브베이즈 분류
library(e1071)
nb_fit = naiveBayes(deposit~., data = train_sub)
nb_fit

test_yhat4 = predict(nb_fit, newdata = test_sub)
test_yhat4

tb4 = table(test$deposit, test_yhat4)
rownames(tb4) = c("true0", "true1")
colnames(tb4) = c("pred0", "pred1")
tb4
# accuracy = (2911+1698)/6578 = 0.700


# Q7. KNN 분류
library(class)
test_yhat5 = knn(train_sub[,-1], test_sub[,-1], train_sub[,1], k=5)

tb5 = table(test$deposit, test_yhat5)
rownames(tb5) = c("true0", "true1")
colnames(tb5) = c("pred0", "pred1")
tb5
# accuracy = (2172+2355)/6578 = 0.688

# Q8. tree model
library(tree)
train_sub$deposit = as.factor(train_sub$deposit)
test_sub$deposit = as.factor(test_sub$deposit)

tree_fit = tree(deposit~., data = train_sub)
summary(tree_fit)

plot(tree_fit)
text(tree_fit, pretty = 0)

test_yhat6 = predict(tree_fit, test_sub, type = "class")

tb6 = table(test$deposit, test_yhat6)
rownames(tb6) = c("true0", "true1")
colnames(tb6) = c("pred0", "pred1")
tb6
# accuracy = (2521+2599)/6578 = 0.778

# Q9. pruning하기
prune = prune.misclass(tree_fit)

plot(prune)
plot(prune$size, prune$dev, xlab = "Size of Tree",
     ylab = "Deviation")

prune_tree = prune.misclass(tree_fit, best = 3)
summary(prune_tree)
plot(prune_tree)
text(prune_tree, pretty = 0)

test_yhat7 = predict(prune_tree, test_sub, type = "class")

tb7 = table(test$deposit, test_yhat7)
rownames(tb7) = c("true0", "true1")
colnames(tb7) = c("pred0", "pred1")
tb7
# accuracy = (1982+2805)/6578 = 0.728


# Q10. 각 방법들의 비교
mean(test_sub$deposit == test_yhat1)  # 로지스틱 (모든변수) 0.821
mean(test_sub$deposit == test_yhat2)  # 변수선택,  로지스틱 0.823 (best)
mean(test_sub$deposit == test_yhat3)  # 선형판별            0.819
mean(test_sub$deposit == test_yhat4)  # 나이브베이즈        0.700
mean(test_sub$deposit == test_yhat5)  # KNN                 0.688
mean(test_sub$deposit == test_yhat6)  # Tree model          0.778
mean(test_sub$deposit == test_yhat7)  # Tree with pruning   0.727

# 이 데이터는 복잡한 모형들 보다는 간단한 모형들에서 더 정확도가 높게 나타난다.




















