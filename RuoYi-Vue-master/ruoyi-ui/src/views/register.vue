<template>
  <div class="register">
    <div class="register-content">
      <h2 class="brand-title">{{ title }}</h2>
      <p class="brand-desc">华设轨道智审系统</p>
      <div class="register-card">
        <h2 class="card-title">注册</h2>
        <p class="card-subtitle">创建您的账号以继续。</p>

        <el-form ref="registerForm" :model="registerForm" :rules="registerRules" class="register-form">
          <!-- 用户名 -->
          <div class="field-label">
            <span class="label-left">用户名</span>
          </div>
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
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
              v-model="registerForm.password"
              type="password"
              auto-complete="off"
              placeholder="请输入密码"
              show-password
              @keyup.enter.native="handleRegister"
            />
          </el-form-item>

          <!-- 确认密码 -->
          <div class="field-label">
            <span class="label-left">确认密码</span>
          </div>
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              auto-complete="off"
              placeholder="请再次输入密码"
              show-password
              @keyup.enter.native="handleRegister"
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
                    v-model="registerForm.code"
                    auto-complete="off"
                    placeholder="请输入验证码"
                    @keyup.enter.native="handleRegister"
                  />
                </el-col>
                <el-col :span="10">
                  <img :src="codeUrl" @click="getCode" class="register-code-img" />
                </el-col>
              </el-row>
            </el-form-item>
          </div>

          <!-- 注册按钮 -->
          <el-form-item>
            <el-button
              :loading="loading"
              type="primary"
              class="register-btn"
              @click.native.prevent="handleRegister"
            >
              <span v-if="!loading">注册</span>
              <span v-else>注册中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部登录提示 -->
        <div class="card-footer">
          已有账号？
          <router-link class="login-link" to="/login">去登录</router-link>
        </div>
      </div>
    </div>

    <div class="el-register-footer">
      <span>{{ footerContent }}</span>
    </div>
  </div>
</template>

<script>
import { getCodeImg, register } from "@/api/login"
import passwordRule from "@/utils/passwordRule"
import defaultSettings from '@/settings'

export default {
  name: "Register",
  mixins: [passwordRule],
  data() {
    return {
      title: process.env.VUE_APP_TITLE,
      footerContent: defaultSettings.footerContent,
      codeUrl: "",
      registerForm: {
        username: "",
        password: "",
        confirmPassword: "",
        code: "",
        uuid: ""
      },
      loading: false,
      captchaEnabled: true
    }
  },
  computed: {
    registerRules() {
      return {
        username: [
          { required: true, trigger: "blur", message: "请输入您的账号" },
          { min: 2, max: 20, message: '用户账号长度必须介于 2 和 20 之间', trigger: 'blur' }
        ],
        password: [
          { required: true, trigger: "blur", message: "请输入您的密码" }
        ],
        confirmPassword: [
          { required: true, message: "请再次输入您的密码", trigger: "blur" },
          {
            validator: (rule, value, callback) => {
              if (this.registerForm.password !== value) {
                callback(new Error("两次输入的密码不一致"))
              } else {
                callback()
              }
            }, trigger: "blur"
          }
        ],
        code: [{ required: true, trigger: "change", message: "请输入验证码" }]
      }
    }
  },
  created() {
    this.getCode()
  },
  methods: {
    getCode() {
      getCodeImg().then(res => {
        this.captchaEnabled = res.captchaEnabled === undefined ? true : res.captchaEnabled
        if (this.captchaEnabled) {
          this.codeUrl = "data:image/gif;base64," + res.img
          this.registerForm.uuid = res.uuid
        }
      })
    },
    handleRegister() {
      this.$refs.registerForm.validate(valid => {
        if (valid) {
          this.loading = true
          register(this.registerForm).then(() => {
            const username = this.registerForm.username
            this.$alert("<font color='red'>恭喜你，您的账号 " + username + " 注册成功！</font>", '系统提示', {
              dangerouslyUseHTMLString: true,
              type: 'success'
            }).then(() => {
              this.$router.push("/login")
            }).catch(() => {})
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

.register {
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

.register-content {
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

.register-card {
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

.register-form {
  ::v-deep .el-form-item {
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

.register-btn {
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

.register-code-img {
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

.login-link {
  color: $primary-dark;
  font-weight: 500;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}

.el-register-footer {
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
