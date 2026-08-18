<template>
  <div class="forgot">
    <div class="forgot-content">
      <h2 class="brand-title">{{ title }}</h2>
      <p class="brand-desc">华设轨道智审系统</p>
      <div class="forgot-card">
        <h2 class="card-title">找回密码</h2>
        <p class="card-subtitle">请输入您的账号，我们将协助您重置密码。</p>

        <el-form ref="forgotForm" :model="forgotForm" :rules="forgotRules" class="forgot-form">
          <!-- 用户名 -->
          <div class="field-label">
            <span class="label-left">用户名</span>
          </div>
          <el-form-item prop="username">
            <el-input
              v-model="forgotForm.username"
              type="text"
              auto-complete="off"
              placeholder="请输入用户名"
            />
          </el-form-item>

          <!-- 邮箱 -->
          <div class="field-label">
            <span class="label-left">邮箱</span>
            <span class="label-right">用于接收重置链接</span>
          </div>
          <el-form-item prop="email">
            <el-input
              v-model="forgotForm.email"
              type="text"
              auto-complete="off"
              placeholder="请输入绑定的邮箱"
            />
          </el-form-item>

          <!-- 提交按钮 -->
          <el-form-item>
            <el-button
              :loading="loading"
              type="primary"
              class="forgot-btn"
              @click.native.prevent="handleSubmit"
            >
              <span v-if="!loading">发送重置链接</span>
              <span v-else>发送中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部返回登录 -->
        <div class="card-footer">
          <router-link class="login-link" to="/login">返回登录</router-link>
        </div>
      </div>
    </div>

    <div class="el-forgot-footer">
      <span>{{ footerContent }}</span>
    </div>
  </div>
</template>

<script>
import defaultSettings from '@/settings'

export default {
  name: "ForgotPassword",
  data() {
    return {
      title: process.env.VUE_APP_TITLE,
      footerContent: defaultSettings.footerContent,
      forgotForm: {
        username: "",
        email: ""
      },
      forgotRules: {
        username: [
          { required: true, trigger: "blur", message: "请输入用户名" }
        ],
        email: [
          { required: true, trigger: "blur", message: "请输入邮箱" },
          { type: "email", trigger: "blur", message: "请输入正确的邮箱格式" }
        ]
      },
      loading: false
    }
  },
  methods: {
    handleSubmit() {
      this.$refs.forgotForm.validate(valid => {
        if (valid) {
          this.loading = true
          setTimeout(() => {
            this.$alert("重置链接已发送至您的邮箱，请注意查收。", '系统提示', {
              type: 'success'
            }).then(() => {
              this.$router.push("/login")
            }).catch(() => {})
            this.loading = false
          }, 1500)
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

.forgot {
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

.forgot-content {
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

.forgot-card {
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
}

.forgot-form {
  ::v-deep .el-form-item {
    margin-bottom: 18px;
  }

  ::v-deep .el-form-item__error {
    top: 48px !important;
    color: #b8605a;
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

.forgot-btn {
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

.el-forgot-footer {
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
