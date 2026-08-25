package com.ruoyi.web.controller.system;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.model.LoginBody;
import com.ruoyi.framework.web.service.SysLoginService;

/**
 * 小程序登录入口：账号密码，免验证码，仅允许拥有小程序登录权限（can_mini=1）的账号登录。
 */
@RestController
public class MiniAppLoginController
{
    @Autowired
    private SysLoginService loginService;

    @PostMapping("/miniapp/login")
    public AjaxResult login(@RequestBody LoginBody loginBody)
    {
        AjaxResult ajax = AjaxResult.success();
        String token = loginService.loginForMiniapp(loginBody.getUsername(), loginBody.getPassword());
        ajax.put(Constants.TOKEN, token);
        return ajax;
    }
}
