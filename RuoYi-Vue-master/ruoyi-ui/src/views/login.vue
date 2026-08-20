<template>
  <div class="login">
    <!-- 背景装饰层：地铁线路网暗纹 -->
    <div class="bg-metro"></div>
    <!-- 背景装饰层：审核对勾 / 文档图标点缀 -->
    <div class="bg-icons"></div>
    <!-- 背景装饰层：城市建筑轮廓剪影 -->
    <div class="bg-buildings"></div>

    <div class="login-card">
      <!-- 系统 Logo 占位 -->
      <div class="login-logo">
        <svg viewBox="0 0 48 48" width="52" height="52" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="loginLogoGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#4da3ff" />
              <stop offset="100%" stop-color="#2563d9" />
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="44" height="44" rx="11" fill="url(#loginLogoGrad)" />
          <path d="M15 11h12l7 7v19a2.5 2.5 0 0 1-2.5 2.5h-16.5A2.5 2.5 0 0 1 12.5 37V13.5A2.5 2.5 0 0 1 15 11z" fill="#ffffff" />
          <path d="M27 11v7h7z" fill="#d6e8ff" />
          <path d="M17 21h12M17 26h12M17 31h7" stroke="#7ba7e8" stroke-width="2" stroke-linecap="round" />
          <circle cx="32" cy="34" r="6.5" fill="#ffffff" />
          <path d="M28.8 34l2.4 2.4 4.4-5" stroke="#2f7de1" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>

      <h3 class="login-title">{{ title }}</h3>
      <p class="login-subtitle">轨道交通政务审核平台</p>

      <el-form ref="loginForm" :model="loginForm" :rules="loginRules" class="login-form">
        <!-- 账号 -->
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            type="text"
            auto-complete="off"
            placeholder="请输入账号"
          >
            <svg-icon slot="prefix" icon-class="user" class="el-input__icon input-icon" />
          </el-input>
        </el-form-item>

        <!-- 密码 -->
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            auto-complete="off"
            placeholder="请输入密码"
            show-password
            @keyup.enter.native="handleLogin"
          >
            <svg-icon slot="prefix" icon-class="password" class="el-input__icon input-icon" />
          </el-input>
        </el-form-item>

        <!-- 验证码 -->
        <el-form-item v-if="captchaEnabled" prop="code">
          <div class="captcha-row">
            <el-input
              v-model="loginForm.code"
              auto-complete="off"
              placeholder="请输入验证码"
              @keyup.enter.native="handleLogin"
            >
              <svg-icon slot="prefix" icon-class="validCode" class="el-input__icon input-icon" />
            </el-input>
            <img
              :src="codeUrl"
              class="login-code-img"
              alt="验证码"
              title="点击图片刷新"
              @click="getCode"
            />
          </div>
        </el-form-item>

        <!-- 记住我 / 忘记密码 -->
        <div class="login-options">
          <el-checkbox v-model="loginForm.rememberMe">记住我</el-checkbox>
          <router-link class="forgot-link" to="/forgot-password">忘记密码？</router-link>
        </div>

        <!-- 登录按钮 -->
        <el-form-item class="btn-item">
          <el-button
            :loading="loading"
            type="primary"
            class="login-btn"
            @click.native.prevent="handleLogin"
          >
            <span v-if="!loading">登 录</span>
            <span v-else>登 录 中...</span>
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 底部版权 -->
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
// Element Plus 风格蓝色系主色调
$primary: #409eff;
$primary-hover: #79bbff;
$primary-active: #337ecc;
$text-main: #303133;
$text-regular: #606266;
$text-muted: #909399;
$border-color: #dcdfe6;

.login {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  // 藏蓝 → 浅天蓝 自上而下线性渐变
  background: linear-gradient(180deg, #13294b 0%, #1b3a67 32%, #2d5d95 58%, #6f9fc9 82%, #c3ddf2 100%);
}

/* ---------- 背景装饰层 ---------- */
.bg-metro,
.bg-icons,
.bg-buildings {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

// 地铁线路网几何暗纹（线路 + 站点）
.bg-metro {
  z-index: 0;
  opacity: 0.13;
  background: url("data:image/svg+xml,%3Csvg width='400' height='400' viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23ffffff' stroke-width='1.5'%3E%3Cpath d='M-40 60H140L230 150H440'/%3E%3Cpath d='M-40 340H120L210 250H300L340 210H440'/%3E%3Cpath d='M80 -40V100L160 180V440'/%3E%3Cpath d='M320 -40V80L400 160V440'/%3E%3Cpath d='M200 -40V60'/%3E%3Cpath d='M-40 200H60'/%3E%3Cpath d='M240 440V360'/%3E%3C/g%3E%3Cg fill='%23ffffff'%3E%3Ccircle cx='80' cy='60' r='3.5'/%3E%3Ccircle cx='140' cy='60' r='3.5'/%3E%3Ccircle cx='230' cy='150' r='3.5'/%3E%3Ccircle cx='80' cy='100' r='3.5'/%3E%3Ccircle cx='160' cy='180' r='3.5'/%3E%3Ccircle cx='120' cy='340' r='3.5'/%3E%3Ccircle cx='210' cy='250' r='3.5'/%3E%3Ccircle cx='300' cy='250' r='3.5'/%3E%3Ccircle cx='340' cy='210' r='3.5'/%3E%3Ccircle cx='320' cy='80' r='3.5'/%3E%3Ccircle cx='400' cy='160' r='3.5'/%3E%3Ccircle cx='200' cy='60' r='3.5'/%3E%3Ccircle cx='60' cy='200' r='3.5'/%3E%3Ccircle cx='240' cy='360' r='3.5'/%3E%3C/g%3E%3C/svg%3E") repeat;
  background-size: 400px 400px;
}

// 若隐若现的审核对勾 / 文档图标点缀
.bg-icons {
  z-index: 0;
  opacity: 0.09;
  background-repeat: no-repeat;
  background-image:
    url("data:image/svg+xml,%3Csvg width='44' height='44' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='22' cy='22' r='18.5' fill='none' stroke='%23ffffff' stroke-width='2.4'/%3E%3Cpath d='M14 22.5l5.5 5.5L30.5 16' fill='none' stroke='%23ffffff' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg width='44' height='44' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='22' cy='22' r='18.5' fill='none' stroke='%23ffffff' stroke-width='2.4'/%3E%3Cpath d='M14 22.5l5.5 5.5L30.5 16' fill='none' stroke='%23ffffff' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg width='44' height='44' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='22' cy='22' r='18.5' fill='none' stroke='%23ffffff' stroke-width='2.4'/%3E%3Cpath d='M14 22.5l5.5 5.5L30.5 16' fill='none' stroke='%23ffffff' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg width='36' height='40' viewBox='0 0 36 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 2h15l8 8v25a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3z' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linejoin='round'/%3E%3Cpath d='M23 2v8h8' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linejoin='round'/%3E%3Cpath d='M10 16h13M10 22h13M10 28h8' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linecap='round'/%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg width='36' height='40' viewBox='0 0 36 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 2h15l8 8v25a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3z' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linejoin='round'/%3E%3Cpath d='M23 2v8h8' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linejoin='round'/%3E%3Cpath d='M10 16h13M10 22h13M10 28h8' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linecap='round'/%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg width='36' height='40' viewBox='0 0 36 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 2h15l8 8v25a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3z' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linejoin='round'/%3E%3Cpath d='M23 2v8h8' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linejoin='round'/%3E%3Cpath d='M10 16h13M10 22h13M10 28h8' fill='none' stroke='%23ffffff' stroke-width='2.2' stroke-linecap='round'/%3E%3C/svg%3E");
  background-position: 4% 18%, 91% 11%, 72% 20%, 83% 42%, 16% 7%, 9% 52%;
  background-size: 46px 46px, 38px 38px, 30px 30px, 36px 40px, 27px 30px, 32px 36px;
}

// 城市建筑轮廓剪影（含轨道高架元素）
.bg-buildings {
  z-index: 0;
  opacity: 0.12;
  background: url("data:image/svg+xml,%3Csvg width='600' height='180' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%2313294b'%3E%3Crect x='0' y='92' width='46' height='88'/%3E%3Crect x='52' y='58' width='34' height='122'/%3E%3Crect x='92' y='112' width='28' height='68'/%3E%3Crect x='126' y='40' width='42' height='140'/%3E%3Crect x='144' y='22' width='3' height='18'/%3E%3Crect x='174' y='96' width='36' height='84'/%3E%3Crect x='216' y='68' width='28' height='112'/%3E%3Crect x='250' y='118' width='44' height='62'/%3E%3Crect x='300' y='52' width='38' height='128'/%3E%3Crect x='316' y='30' width='3' height='22'/%3E%3Crect x='344' y='102' width='32' height='78'/%3E%3Crect x='382' y='34' width='46' height='146'/%3E%3Crect x='434' y='88' width='30' height='92'/%3E%3Crect x='470' y='116' width='40' height='64'/%3E%3Crect x='516' y='62' width='34' height='118'/%3E%3Crect x='530' y='42' width='3' height='20'/%3E%3Crect x='556' y='96' width='44' height='84'/%3E%3C/g%3E%3C/svg%3E") repeat-x bottom center;
  background-size: 600px 180px;
}

/* ---------- 登录卡片 ---------- */
.login-card {
  position: relative;
  z-index: 2;
  width: 420px;
  max-width: calc(100vw - 32px);
  padding: 40px 42px 36px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow:
    0 12px 36px rgba(35, 82, 148, 0.16),
    0 3px 10px rgba(35, 82, 148, 0.08);
}

.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 14px;

  svg {
    filter: drop-shadow(0 4px 10px rgba(37, 99, 217, 0.28));
  }
}

.login-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 600;
  color: #1f2d3d;
  text-align: center;
  letter-spacing: 2px;
}

.login-subtitle {
  margin: 0 0 30px;
  font-size: 13px;
  color: #8c9bab;
  text-align: center;
  letter-spacing: 4px;
}

/* ---------- 表单（Element Plus 风格） ---------- */
.login-form {
  ::v-deep .el-form-item {
    margin-bottom: 20px;
  }

  ::v-deep .el-form-item__error {
    padding-top: 2px;
  }

  ::v-deep .el-input__inner {
    height: 40px;
    line-height: 40px;
    border-radius: 4px;
    border: 1px solid $border-color;
    color: $text-main;
    transition: border-color 0.2s ease;

    &::placeholder {
      color: #a8abb2;
    }

    &:hover {
      border-color: #c0c4cc;
    }

    &:focus {
      border-color: $primary;
    }
  }

  // 前缀图标（账号 / 密码 / 验证码）
  ::v-deep .el-input__prefix {
    left: 11px;
    display: flex;
    align-items: center;
    color: $text-muted;
  }

  ::v-deep .el-input--prefix .el-input__inner {
    padding-left: 36px;
  }
}

.input-icon {
  width: 16px;
  height: 16px;
  margin-left: 2px;
}

/* ---------- 验证码行 ---------- */
.captcha-row {
  display: flex;
  align-items: center;
  width: 100%;

  ::v-deep .el-input {
    flex: 1;
  }
}

.login-code-img {
  width: 118px;
  height: 40px;
  margin-left: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #f5f7fa;
  cursor: pointer;
  transition: border-color 0.2s ease;

  &:hover {
    border-color: $primary;
  }
}

/* ---------- 记住我 / 忘记密码 ---------- */
.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 22px;

  ::v-deep .el-checkbox {
    .el-checkbox__label {
      font-size: 13px;
      color: $text-regular;
    }

    .el-checkbox__input.is-checked .el-checkbox__inner {
      background-color: $primary;
      border-color: $primary;
    }

    &:hover .el-checkbox__inner {
      border-color: $primary;
    }
  }
}

.forgot-link {
  font-size: 13px;
  color: $text-muted;
  text-decoration: none;
  transition: color 0.2s ease;

  &:hover {
    color: $primary;
  }
}

/* ---------- 登录按钮 ---------- */
.login-form ::v-deep .btn-item {
  margin-bottom: 0;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 2px;
  border: 1px solid $primary;
  border-radius: 4px;
  background: $primary;
  transition: background-color 0.2s ease, border-color 0.2s ease;

  &:hover,
  &:focus {
    background: $primary-hover;
    border-color: $primary-hover;
  }

  &:active {
    background: $primary-active;
    border-color: $primary-active;
  }
}

/* ---------- 底部版权 ---------- */
.el-login-footer {
  position: fixed;
  bottom: 16px;
  width: 100%;
  text-align: center;
  font-size: 12px;
  letter-spacing: 1px;
  color: rgba(35, 67, 105, 0.65);
  z-index: 2;
}

/* ---------- 小屏适配 ---------- */
@media (max-width: 480px) {
  .login-card {
    width: 100%;
    padding: 32px 26px 28px;
  }
}
</style>
