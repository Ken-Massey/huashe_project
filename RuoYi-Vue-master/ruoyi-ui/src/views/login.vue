<template>
  <div class="login">
    <div class="login-content">
      <h2 class="brand-title">{{ title }}</h2>
      <p class="brand-desc">华设轨道智审系统</p>
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
$primary: #6b92c0;
$primary-dark: #4e76a8;
$primary-light: #9dbdd8;
$text-dark: #2c4a6a;
$text-body: #4a6a8a;
$text-muted: #7a96b2;
$border: #b8cce0;
$card-bg: linear-gradient(145deg, rgba(180, 205, 228, 0.9) 0%, rgba(200, 222, 242, 0.93) 50%, rgba(170, 198, 225, 0.9) 100%);

.login {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: linear-gradient(135deg, #c8d8ea 0%, #dce8f4 25%, #e8f0f8 50%, #d0e0f0 75%, #c0d4e8 100%);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
      linear-gradient(125deg, transparent 30%, rgba(255,255,255,0.4) 30.5%, rgba(255,255,255,0.4) 31%, transparent 31.5%),
      linear-gradient(125deg, transparent 60%, rgba(200,218,238,0.5) 60.5%, rgba(200,218,238,0.5) 61%, transparent 61.5%),
      linear-gradient(125deg, transparent 80%, rgba(255,255,255,0.3) 80.5%, rgba(255,255,255,0.3) 81%, transparent 81.5%);
    pointer-events: none;
  }

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.15'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
    pointer-events: none;
  }
}

.login-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 580px;
  padding: 0 24px;
  margin-top: 10vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  letter-spacing: 4px;
  color: $text-dark;
  text-shadow: 0 1px 3px rgba(255, 255, 255, 0.6);
}

.brand-desc {
  font-size: 16px;
  margin: 0 0 40px 0;
  color: $text-muted;
  opacity: 0.9;
  letter-spacing: 4px;
}

.login-card {
  width: 100%;
  padding: 40px 56px;
  background: $card-bg;
  border-radius: 24px;
  box-shadow:
    0 8px 32px rgba(122, 158, 200, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.7),
    inset 0 -1px 0 rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(24px) saturate(1.4);
  -webkit-backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.6);
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.3s ease, transform 0.3s ease;

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(
      ellipse at 30% 20%,
      rgba(255, 255, 255, 0.25) 0%,
      transparent 50%
    );
    pointer-events: none;
  }

  &:hover {
    box-shadow:
      0 12px 40px rgba(122, 158, 200, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.8),
      inset 0 -1px 0 rgba(255, 255, 255, 0.4);
    transform: translateY(-2px);
  }
}

.card-title {
  margin: 0 0 6px 0;
  font-size: 28px;
  font-weight: 700;
  color: $text-dark;
  text-align: left;
}

.card-subtitle {
  margin: 0 0 28px 0;
  font-size: 14px;
  color: $text-muted;
  text-align: left;
}

.field-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.label-left {
  font-size: 14px;
  font-weight: 600;
  color: $text-body;
}

.label-right {
  font-size: 13px;
  color: $text-muted;
  cursor: pointer;

  &:hover {
    color: $primary;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 18px;
  }

  ::v-deep .el-form-item__error {
    top: 48px !important;
    color: #b8605a;
  }

  ::v-deep .el-row {
    margin-left: 0 !important;
    margin-right: 0 !important;

    .el-col {
      padding-left: 0 !important;
      padding-right: 0 !important;
    }

    .el-col:first-child {
      padding-right: 8px !important;
    }

    .el-col:last-child {
      padding-left: 8px !important;
    }

    .el-col:first-child {
      .el-input {
        height: 48px;
        line-height: 48px;

        .el-input__inner {
          height: 48px;
          line-height: 48px;
        }
      }
    }
  }

  ::v-deep .el-input {
    height: 48px;
    line-height: 48px;

    .el-input__inner {
      height: 48px;
      line-height: 48px;
      border-radius: 12px;
      font-size: 15px;
      border: 1.5px solid $border;
      background: rgba(255, 255, 255, 0.5);
      padding: 0 18px;
      color: $text-body;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &::placeholder {
        color: $text-muted;
        font-size: 14px;
      }

      &:hover {
        border-color: $primary;
        background: rgba(255, 255, 255, 0.7);
      }

      &:focus {
        border: 2px solid $primary;
        background: rgba(255, 255, 255, 0.8);
        box-shadow: 0 0 0 3px rgba(123, 158, 200, 0.15);
        outline: none;
      }
    }
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  margin-top: -8px;

  ::v-deep .el-checkbox {
    .el-checkbox__label {
      font-size: 14px;
      color: $primary-dark;
      font-weight: 500;
    }

    .el-checkbox__input.is-checked .el-checkbox__inner {
      background-color: $primary;
      border-color: $primary;
    }

    .el-checkbox__input.is-checked + .el-checkbox__label {
      color: $primary-dark;
    }

    &:hover {
      .el-checkbox__inner {
        border-color: $primary;
      }
    }
  }
}

.forgot-link {
  font-size: 14px;
  color: $primary-dark;
  text-decoration: none;
  font-weight: 500;

  &:hover {
    color: $primary;
    text-decoration: underline;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 6px;
  background: linear-gradient(135deg, $primary 0%, $primary-dark 100%);
  border: none;
  color: #fff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: linear-gradient(135deg, $primary-light 0%, $primary 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(123, 158, 200, 0.35);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(123, 158, 200, 0.25);
  }
}

.login-code-img {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  cursor: pointer;
  object-fit: cover;
  border: 1.5px solid $border;
  background: rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    border-color: $primary;
    box-shadow: 0 0 8px rgba(123, 158, 200, 0.15);
  }

  &:active {
    border: 2px solid $primary;
    box-shadow: 0 0 0 3px rgba(123, 158, 200, 0.15);
  }
}

.card-footer {
  margin-top: 28px;
  text-align: center;
  font-size: 14px;
  color: $text-muted;
}

.register-link {
  color: $primary-dark;
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
  color: $text-muted;
  font-size: 12px;
  letter-spacing: 1px;
  z-index: 10;
}
</style>
