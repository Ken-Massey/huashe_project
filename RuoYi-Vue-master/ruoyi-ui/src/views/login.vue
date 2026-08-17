<template>
  <div class="login">
    <!-- 左侧 50% 品牌展示区 -->
    <div class="login-left">
      <div class="left-content">
        <h2 class="brand-title">{{ title }}</h2>
        <p class="brand-desc">华设轨道智审系统</p>
      </div>
    </div>
    <!-- 右侧 50% 登录区 -->
    <div class="login-right">
      <div class="login-card">
        <h2 class="card-title">登录</h2>
        <p class="card-subtitle">请输入用户名与密码以继续。</p>

        <el-form ref="loginForm" :model="loginForm" :rules="loginRules" class="login-form">
          <!-- 用户名 -->
          <div class="field-label">
            <span class="label-left">用户名</span>

          </div>
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              type="text"
              auto-complete="off"
              placeholder="请输入用户名"
            />
          </el-form-item>

          <!-- 密码 -->
          <div class="field-label">
            <span class="label-left">密码</span>

          </div>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              auto-complete="off"
              placeholder="请输入密码"
              show-password
              @keyup.enter.native="handleLogin"
            />
          </el-form-item>

          <!-- 验证码 -->
          <div v-if="captchaEnabled">
            <div class="field-label">
              <span class="label-left">验证码</span>
              <span class="label-right">点击图片刷新</span>
            </div>
            <el-form-item prop="code">
              <el-row :gutter="16">
                <el-col :span="14">
                  <el-input
                    v-model="loginForm.code"
                    auto-complete="off"
                    placeholder="请输入验证码"
                    @keyup.enter.native="handleLogin"
                  />
                </el-col>
                <el-col :span="10">
                  <img :src="codeUrl" @click="getCode" class="login-code-img" />
                </el-col>
              </el-row>
            </el-form-item>
          </div>

          <!-- 记住我 / 忘记密码 -->
          <div class="login-options">
            <el-checkbox v-model="loginForm.rememberMe">记住我</el-checkbox>
            <router-link class="forgot-link" to="/forgot-password">忘记密码?</router-link>
          </div>

          <!-- 登录按钮 -->
          <el-form-item>
            <el-button
              :loading="loading"
              type="primary"
              class="login-btn"
              @click.native.prevent="handleLogin"
            >
              <span v-if="!loading">登录</span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部注册提示 -->
        <div class="card-footer">
          没有账号？
          <router-link class="register-link" to="/register">注册</router-link>
        </div>
      </div>
    </div>

    <div class="el-login-footer">
      <span>{{ footerContent }}</span>
    </div>
  </div>
</template>

<script>
import { getCodeImg } from "@/api/login"
import Cookies from "js-cookie"
import { encrypt, decrypt } from '@/utils/jsencrypt'
import defaultSettings from '@/settings'

export default {
  name: "Login",
  data() {
    return {
      title: process.env.VUE_APP_TITLE,
      footerContent: defaultSettings.footerContent,
      codeUrl: "",
      loginForm: {
        username: "admin",
        password: "admin123",
        rememberMe: false,
        code: "",
        uuid: ""
      },
      loginRules: {
        username: [
          { required: true, trigger: "blur", message: "请输入您的账号" }
        ],
        password: [
          { required: true, trigger: "blur", message: "请输入您的密码" }
        ],
        code: [{ required: true, trigger: "change", message: "请输入验证码" }]
      },
      loading: false,
      captchaEnabled: true,
      register: false,
      redirect: undefined
    }
  },
  watch: {
    $route: {
      handler: function(route) {
        this.redirect = route.query && route.query.redirect
      },
      immediate: true
    }
  },
  created() {
    this.getCode()
    this.getCookie()
  },
  methods: {
    getCode() {
      getCodeImg().then(res => {
        this.captchaEnabled = res.captchaEnabled === undefined ? true : res.captchaEnabled
        if (this.captchaEnabled) {
          this.codeUrl = "data:image/gif;base64," + res.img
          this.loginForm.uuid = res.uuid
        }
      }).catch(() => {})
    },
    getCookie() {
      const username = Cookies.get("username")
      const password = Cookies.get("password")
      const rememberMe = Cookies.get('rememberMe')
      this.loginForm = {
        username: username === undefined ? this.loginForm.username : username,
        password: password === undefined ? this.loginForm.password : decrypt(password),
        rememberMe: rememberMe === undefined ? false : Boolean(rememberMe)
      }
    },
    handleLogin() {
      this.$refs.loginForm.validate(valid => {
        if (valid) {
          this.loading = true
          if (this.loginForm.rememberMe) {
            Cookies.set("username", this.loginForm.username, { expires: 30 })
            Cookies.set("password", encrypt(this.loginForm.password), { expires: 30 })
            Cookies.set('rememberMe', this.loginForm.rememberMe, { expires: 30 })
          } else {
            Cookies.remove("username")
            Cookies.remove("password")
            Cookies.remove('rememberMe')
          }
          this.$store.dispatch("Login", this.loginForm).then(() => {
            this.$router.push({ path: this.redirect || "/" }).catch(()=>{})
          }).catch(() => {
            this.loading = false
            if (this.captchaEnabled) {
              this.getCode()
            }
          })
        }
      })
    }
  }
}
</script>

<style rel="stylesheet/scss" lang="scss" scoped>
.login {
  display: flex;
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
}

/* ===== 左侧品牌区 50% ===== */
.login-left {
  width: 50%;
  height: 100vh;
  min-height: 100vh;
  background-image: url("../assets/images/login-background.jpg");
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  position: relative;
  opacity: 0.8;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(30, 80, 162, 0.35) 0%, rgba(0, 0, 0, 0.15) 100%);
  }
}

.left-content {
  position: relative;
  z-index: 1;
  padding: 0 56px;
  color: #fff;
}

.brand-logo {
  width: 56px;
  height: 56px;
  margin-bottom: 20px;
  filter: brightness(0) invert(1);
}

.brand-title {
  font-size: 30px;
  font-weight: 700;
  margin: 0 0 8px 0;
  letter-spacing: 2px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}

.brand-desc {
  font-size: 16px;
  margin: 0;
  opacity: 0.85;
  letter-spacing: 4px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.2);
}

/* ===== 右侧登录区 50% ===== */
.login-right {
  width: 50%;
  height: 100vh;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fc;
}

.login-card {
  width: 80%;
  max-width: 800px;
  padding: 130px 72px;
  background: #fff;
  border-radius: 32px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.3s ease, transform 0.3s ease;

  &:hover {
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
  }
}

.card-title {
  margin: 0 0 8px 0;
  font-size: 38px;
  font-weight: 700;
  color: #1a1a2e;
  text-align: left;
}

.card-subtitle {
  margin: 0 0 48px 0;
  font-size: 16px;
  color: #909399;
  text-align: left;
}

.field-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.label-left {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.label-right {
  font-size: 14px;
  color: #b0b3c6;
  cursor: pointer;

  &:hover {
    color: #5b6abf;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 28px;
  }

  ::v-deep .el-row {
    .el-col:first-child {
      .el-input {
        height: 56px;
        line-height: 56px;

        .el-input__inner {
          height: 56px;
          line-height: 56px;
        }
      }
    }
  }

  ::v-deep .el-input {
    height: 56px;
    line-height: 56px;

    .el-input__inner {
      height: 56px;
      line-height: 56px;
      border-radius: 12px;
      font-size: 16px;
      border: 1.5px solid #e8e9ed;
      padding: 0 16px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &::placeholder {
        color: #c0c4cc;
      }

      &:hover {
        border-color: #5b6abf;
      }

      &:focus {
        border: 2px solid #5b6abf;
        box-shadow: 0 0 0 4px rgba(91, 106, 191, 0.18), 0 0 12px rgba(91, 106, 191, 0.12);
        outline: none;
      }
    }
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 36px;
  margin-top: -8px;

  ::v-deep .el-checkbox {
    .el-checkbox__label {
      font-size: 15px;
      color: #5b6abf;
      font-weight: 500;
    }

    .el-checkbox__input.is-checked .el-checkbox__inner {
      background-color: #5b6abf;
      border-color: #5b6abf;
    }

    .el-checkbox__input.is-checked + .el-checkbox__label {
      color: #5b6abf;
    }

    &:hover {
      .el-checkbox__inner {
        border-color: #5b6abf;
      }
    }
  }
}

.forgot-link {
  font-size: 15px;
  color: #5b6abf;
  text-decoration: none;
  font-weight: 500;

  &:hover {
    color: #4a58a0;
    text-decoration: underline;
  }
}

.login-btn {
  width: 100%;
  height: 60px;
  border-radius: 14px;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 6px;
  background: linear-gradient(135deg, #5b6abf 0%, #4a58a0 100%);
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: linear-gradient(135deg, #6e7dd4 0%, #5b6abf 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(91, 106, 191, 0.35);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(91, 106, 191, 0.25);
  }
}

.login-code-img {
  width: 100%;
  height: 56px;
  border-radius: 12px;
  cursor: pointer;
  object-fit: cover;
  border: 1.5px solid #e8e9ed;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    border-color: #5b6abf;
    box-shadow: 0 0 8px rgba(91, 106, 191, 0.15);
  }

  &:active {
    border: 2px solid #5b6abf;
    box-shadow: 0 0 0 4px rgba(91, 106, 191, 0.18), 0 0 12px rgba(91, 106, 191, 0.12);
  }
}

.card-footer {
  margin-top: 36px;
  text-align: center;
  font-size: 15px;
  color: #909399;
}

.register-link {
  color: #5b6abf;
  font-weight: 500;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}

.el-login-footer {
  height: 40px;
  line-height: 40px;
  position: fixed;
  bottom: 0;
  width: 100%;
  text-align: center;
  color: #909399;
  font-size: 12px;
  letter-spacing: 1px;
  z-index: 10;
}
</style>
