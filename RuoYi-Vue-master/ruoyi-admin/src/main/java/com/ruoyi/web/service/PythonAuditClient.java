package com.ruoyi.web.service;

import java.io.ByteArrayOutputStream;
import java.util.Collections;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.util.UriComponentsBuilder;
import com.alibaba.fastjson2.JSON;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.web.config.PythonAuditProperties;

/** Internal HTTP client for the Python audit service. */
@Service
public class PythonAuditClient
{
    private final RestClient client;
    private final HttpClient uploadClient;
    private final String baseUrl;
    private final String token;

    public PythonAuditClient(PythonAuditProperties properties)
    {
        this.baseUrl = properties.getBaseUrl().replaceAll("/+$", "");
        this.token = properties.getToken();
        this.uploadClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(15))
                .build();
        RestClient.Builder builder = RestClient.builder().baseUrl(baseUrl);
        if (StringUtils.isNotEmpty(properties.getToken()))
        {
            builder.defaultHeader("X-Service-Token", properties.getToken());
        }
        this.client = builder.build();
    }

    public Object postFiles(String path, Map<String, MultipartFile> files, Map<String, String> fields)
    {
        return postFiles(path, files, fields, Collections.emptyMap(), Collections.emptyMap());
    }

    public Object postFiles(String path, Map<String, MultipartFile> files, Map<String, String> fields,
            Map<String, MultipartFile[]> multiFiles)
    {
        return postFiles(path, files, fields, multiFiles, Collections.emptyMap());
    }

    public Object postFiles(String path, Map<String, MultipartFile> files, Map<String, String> fields,
            Map<String, MultipartFile[]> multiFiles, Map<String, String> headers)
    {
        try
        {
            String boundary = "----RuoYiAudit" + UUID.randomUUID().toString().replace("-", "");
            byte[] body = multipart(boundary, files, fields, multiFiles);
            HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(baseUrl + path))
                    .timeout(Duration.ofMinutes(3))
                    .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                    .POST(HttpRequest.BodyPublishers.ofByteArray(body));
            if (StringUtils.isNotEmpty(token))
            {
                request.header("X-Service-Token", token);
            }
            if (headers != null)
            {
                headers.forEach(request::header);
            }
            HttpResponse<String> response = uploadClient.send(
                    request.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() < 200 || response.statusCode() >= 300)
            {
                throw new ServiceException("智能审核服务返回错误（" + response.statusCode() + "）：" + response.body());
            }
            return StringUtils.isEmpty(response.body()) ? Map.of() : JSON.parse(response.body());
        }
        catch (ServiceException exception)
        {
            throw exception;
        }
        catch (InterruptedException exception)
        {
            Thread.currentThread().interrupt();
            throw new ServiceException("上传任务已中断。");
        }
        catch (Exception exception)
        {
            throw new ServiceException("转发上传文件失败：" + exception.getMessage());
        }
    }

    public Object get(String path)
    {
        return json(() -> client.get().uri(path).retrieve().body(String.class));
    }

    public Object get(String path, Map<String, ?> query)
    {
        UriComponentsBuilder uri = UriComponentsBuilder.fromPath(path);
        query.forEach((name, value) -> {
            if (value != null)
            {
                uri.queryParam(name, value);
            }
        });
        return get(uri.build().encode().toUriString());
    }

    public Object get(String path, Map<String, ?> query, Map<String, String> headers)
    {
        UriComponentsBuilder uri = UriComponentsBuilder.fromPath(path);
        if (query != null)
        {
            query.forEach((name, value) -> {
                if (value != null)
                {
                    uri.queryParam(name, value);
                }
            });
        }
        return json(() -> {
            org.springframework.web.client.RestClient.RequestHeadersSpec<?> request =
                    client.get().uri(uri.build().encode().toUriString());
            if (headers != null && !headers.isEmpty())
            {
                request.headers(httpHeaders -> headers.forEach(httpHeaders::add));
            }
            return request.retrieve().body(String.class);
        });
    }

    public Object post(String path)
    {
        return json(() -> client.post().uri(path).retrieve().body(String.class));
    }

    public Object post(String path, Object body)
    {
        return post(path, body, Collections.emptyMap());
    }

    public Object post(String path, Object body, Map<String, String> headers)
    {
        try
        {
            byte[] payload = JSON.toJSONString(body).getBytes(StandardCharsets.UTF_8);
            HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(baseUrl + path))
                    .timeout(Duration.ofMinutes(3))
                    .header("Content-Type", "application/json; charset=UTF-8")
                    .POST(HttpRequest.BodyPublishers.ofByteArray(payload));
            if (StringUtils.isNotEmpty(token))
            {
                request.header("X-Service-Token", token);
            }
            if (headers != null)
            {
                headers.forEach(request::header);
            }
            HttpResponse<String> response = uploadClient.send(
                    request.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() < 200 || response.statusCode() >= 300)
            {
                throw new ServiceException("智能审核服务返回错误（" + response.statusCode() + "）：" + response.body());
            }
            return StringUtils.isEmpty(response.body()) ? Map.of() : JSON.parse(response.body());
        }
        catch (ServiceException exception)
        {
            throw exception;
        }
        catch (InterruptedException exception)
        {
            Thread.currentThread().interrupt();
            throw new ServiceException("智能体请求已中断。");
        }
        catch (Exception exception)
        {
            throw new ServiceException("智能体服务连接失败：" + exception.getMessage());
        }
    }

    public Object delete(String path)
    {
        return json(() -> client.delete().uri(path).retrieve().body(String.class));
    }

    public Object delete(String path, Map<String, String> headers)
    {
        return json(() -> {
            org.springframework.web.client.RestClient.RequestHeadersSpec<?> request = client.delete().uri(path);
            if (headers != null && !headers.isEmpty())
            {
                request.headers(httpHeaders -> headers.forEach(httpHeaders::add));
            }
            return request.retrieve().body(String.class);
        });
    }

    public ResponseEntity<byte[]> download(String path)
    {
        return download(path, null);
    }

    /** 携带操作者身份头下载（Python 端做行级隔离校验）。 */
    public ResponseEntity<byte[]> download(String path, Map<String, String> headers)
    {
        try
        {
            RestClient.RequestHeadersSpec<?> request = client.get().uri(path);
            if (headers != null && !headers.isEmpty())
            {
                request.headers(httpHeaders -> headers.forEach(httpHeaders::add));
            }
            return request.retrieve().toEntity(byte[].class);
        }
        catch (RestClientResponseException exception)
        {
            throw pythonError(exception);
        }
    }

    public ResponseEntity<byte[]> postDownload(String path, Object body)
    {
        try
        {
            byte[] payload = JSON.toJSONString(body).getBytes(StandardCharsets.UTF_8);
            HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(baseUrl + path))
                    .timeout(Duration.ofMinutes(3))
                    .header("Content-Type", "application/json; charset=UTF-8")
                    .POST(HttpRequest.BodyPublishers.ofByteArray(payload));
            if (StringUtils.isNotEmpty(token))
            {
                request.header("X-Service-Token", token);
            }
            HttpResponse<byte[]> response = uploadClient.send(
                    request.build(), HttpResponse.BodyHandlers.ofByteArray());
            if (response.statusCode() < 200 || response.statusCode() >= 300)
            {
                String detail = new String(response.body(), StandardCharsets.UTF_8);
                throw new ServiceException("智能审核服务返回错误（" + response.statusCode() + "）：" + detail);
            }
            HttpHeaders headers = new HttpHeaders();
            response.headers().firstValue("content-type")
                    .ifPresent(value -> headers.setContentType(MediaType.parseMediaType(value)));
            response.headers().firstValue("content-disposition")
                    .ifPresent(value -> headers.set(HttpHeaders.CONTENT_DISPOSITION, value));
            return ResponseEntity.ok().headers(headers).body(response.body());
        }
        catch (ServiceException exception)
        {
            throw exception;
        }
        catch (InterruptedException exception)
        {
            Thread.currentThread().interrupt();
            throw new ServiceException("文件生成请求已中断。");
        }
        catch (Exception exception)
        {
            throw new ServiceException("智能审核服务连接失败：" + exception.getMessage());
        }
    }

    private Object json(JsonRequest request)
    {
        try
        {
            String body = request.execute();
            return StringUtils.isEmpty(body) ? Map.of() : JSON.parse(body);
        }
        catch (RestClientResponseException exception)
        {
            throw pythonError(exception);
        }
        catch (Exception exception)
        {
            throw new ServiceException("智能审核服务连接失败：" + exception.getMessage());
        }
    }

    private ServiceException pythonError(RestClientResponseException exception)
    {
        String detail = exception.getResponseBodyAsString();
        if (StringUtils.isEmpty(detail))
        {
            detail = exception.getStatusText();
        }
        return new ServiceException("智能审核服务返回错误（" + exception.getStatusCode().value() + "）：" + detail);
    }

    private byte[] multipart(String boundary, Map<String, MultipartFile> files, Map<String, String> fields,
            Map<String, MultipartFile[]> multiFiles)
    {
        try
        {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            for (Map.Entry<String, String> entry : fields.entrySet())
            {
                if (entry.getValue() == null)
                {
                    continue;
                }
                write(output, "--" + boundary + "\r\n");
                write(output, "Content-Disposition: form-data; name=\"" + quote(entry.getKey()) + "\"\r\n");
                write(output, "Content-Type: text/plain; charset=UTF-8\r\n\r\n");
                write(output, entry.getValue());
                write(output, "\r\n");
            }
            for (Map.Entry<String, MultipartFile> entry : files.entrySet())
            {
                writeFilePart(output, boundary, entry.getKey(), entry.getValue());
            }
            for (Map.Entry<String, MultipartFile[]> entry : multiFiles.entrySet())
            {
                MultipartFile[] values = entry.getValue();
                if (values == null)
                {
                    continue;
                }
                for (MultipartFile file : values)
                {
                    writeFilePart(output, boundary, entry.getKey(), file);
                }
            }
            write(output, "--" + boundary + "--\r\n");
            return output.toByteArray();
        }
        catch (Exception exception)
        {
            throw new ServiceException("读取上传文件失败：" + exception.getMessage());
        }
    }

    private void writeFilePart(ByteArrayOutputStream output, String boundary, String name, MultipartFile file)
            throws Exception
    {
        if (file == null || file.isEmpty())
        {
            return;
        }
        write(output, "--" + boundary + "\r\n");
        write(output, "Content-Disposition: form-data; name=\"" + quote(name)
                + "\"; filename=\"" + quote(safeFilename(file)) + "\"\r\n");
        write(output, "Content-Type: " + (StringUtils.isEmpty(file.getContentType())
                ? MediaType.APPLICATION_OCTET_STREAM_VALUE : file.getContentType()) + "\r\n\r\n");
        output.write(file.getBytes());
        write(output, "\r\n");
    }

    private void write(ByteArrayOutputStream output, String value)
    {
        output.writeBytes(value.getBytes(StandardCharsets.UTF_8));
    }

    private String quote(String value)
    {
        return value.replace("\\", "_").replace("\"", "_").replace("\r", "_").replace("\n", "_");
    }

    private String safeFilename(MultipartFile file)
    {
        String name = file.getOriginalFilename();
        return StringUtils.isEmpty(name) ? "document" : name.replace("\\", "_").replace("/", "_");
    }

    @FunctionalInterface
    private interface JsonRequest
    {
        String execute();
    }
}
