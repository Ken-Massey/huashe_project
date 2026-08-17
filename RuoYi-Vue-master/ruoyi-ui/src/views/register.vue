<template>
  <div class="register">
    <!-- 左侧品牌展示区 -->
    <div class="register-left">
      <div class="left-content">
        <h2 class="brand-title">{{ title }}</h2>
        <p class="brand-desc">华设轨道智审系统</p>
      </div>
    </div>
    <!-- 右侧注册区 -->
    <div class="register-right">
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
            <span class="label-right">区分大小写</span>
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
.register {
  display: flex;
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
}

/* ===== 左侧品牌区 50% ===== */
.register-left {
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
  opacity: 0.8;
  letter-spacing: 4px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.2);
}

/* ===== 右侧注册区 50% ===== */
.register-right {
  width: 50%;
  height: 100vh;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fc;
}

.register-card {
  width: 80%;
  max-width: 800px;
  padding: 80px 72px;
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

.register-form {
  ::v-deep .el-form-item {
    margin-bottom: 24px;
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

.register-btn {
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

.register-code-img {
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

.login-link {
  color: #5b6abf;
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
  color: #909399;
  font-size: 12px;
  letter-spacing: 1px;
  z-index: 10;
}
</style>
