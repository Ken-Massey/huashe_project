<template>
  <div class="forgot">
    <div class="forgot-left">
      <div class="left-content">
        <h2 class="brand-title">{{ title }}</h2>
        <p class="brand-desc">华设轨道智审系统</p>
      </div>
    </div>
    <div class="forgot-right">
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
.forgot {
  display: flex;
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
}

.forgot-left {
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

.forgot-right {
  width: 50%;
  height: 100vh;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fc;
}

.forgot-card {
  width: 80%;
  max-width: 800px;
  padding: 100px 72px;
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
}

.forgot-form {
  ::v-deep .el-form-item {
    margin-bottom: 28px;
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

.forgot-btn {
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

.card-footer {
  margin-top: 36px;
  text-align: center;
  font-size: 15px;
}

.login-link {
  color: #5b6abf;
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
  color: #909399;
  font-size: 12px;
  letter-spacing: 1px;
  z-index: 10;
}
</style>
