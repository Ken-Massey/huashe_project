package com.ruoyi.web.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/** Python intelligent audit service settings. */
@Component
@ConfigurationProperties(prefix = "audit.python")
public class PythonAuditProperties
{
    private String baseUrl = "http://127.0.0.1:8000";
    private String token = "";

    public String getBaseUrl() { return baseUrl; }
    public void setBaseUrl(String baseUrl) { this.baseUrl = baseUrl; }
    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
}
