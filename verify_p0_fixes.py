"""P0 安全修复验证脚本：空身份不提权 + 媒体上传行级隔离"""
import requests
import io
from PIL import Image

BASE = "http://127.0.0.1:8000"
SVC = {"X-Service-Token": "dev-service-token"}

# ========== 验证 P0-#4: 空 user_id 不再默认管理员 ==========
print("=== P0-#4: empty identity is not admin ===")
r = requests.get(f"{BASE}/api/v1/patrol/tasks", headers=SVC)
data = r.json()
empty_count = data.get("total", 0)
print(f"  no X-Actor headers list tasks: total={empty_count} (expect 0)")
assert empty_count == 0, f"FAIL: empty identity sees {empty_count} tasks!"
print("  PASS")

# admin creates two tasks assigned to different patrol users
admin = {**SVC, "X-Actor-User-Id": "1", "X-Actor-Name": "admin", "X-Actor-Is-Admin": "true"}
t1 = requests.post(f"{BASE}/api/v1/patrol/tasks", headers=admin, json={
    "name": "isolation-test-A", "line": "L1", "location_desc": "point-A",
    "assigned_user_id": "100", "assigned_user_name": "patrol-A"
}).json()
t2 = requests.post(f"{BASE}/api/v1/patrol/tasks", headers=admin, json={
    "name": "isolation-test-B", "line": "L2", "location_desc": "point-B",
    "assigned_user_id": "200", "assigned_user_name": "patrol-B"
}).json()
print(f"  taskA={t1['task_id']} -> user100, taskB={t2['task_id']} -> user200")

# patrol user A creates a record under task A
a_headers = {**SVC, "X-Actor-User-Id": "100", "X-Actor-Name": "patrol-A", "X-Actor-Is-Admin": "false"}
rec = requests.post(f"{BASE}/api/v1/patrol/tasks/{t1['task_id']}/records", headers=a_headers, json={
    "type": "patrol", "note": "record-by-A"
}).json()
print(f"  user100 created record: {rec['record_id']}")

# ========== 验证 P0-#1: media upload row-level isolation ==========
print()
print("=== P0-#1: media upload row-level isolation ===")

# patrol user B tries to upload to A's record -> should be 404
img = Image.new("RGB", (100, 100), color="red")
buf = io.BytesIO()
img.save(buf, format="JPEG")
buf.seek(0)
b_headers = {**SVC, "X-Actor-User-Id": "200", "X-Actor-Name": "patrol-B", "X-Actor-Is-Admin": "false"}
r = requests.post(f"{BASE}/api/v1/patrol/records/{rec['record_id']}/media",
    headers=b_headers, files={"file": ("test.jpg", buf, "image/jpeg")}, data={"kind": "photo"})
print(f"  user200 upload to user100 record: status={r.status_code} (expect 404)")
assert r.status_code == 404, f"FAIL: user200 can upload to other's record! status={r.status_code} body={r.text}"
print("  PASS")

# patrol user A uploads to own record -> should be 201
buf2 = io.BytesIO()
img.save(buf2, format="JPEG")
buf2.seek(0)
r = requests.post(f"{BASE}/api/v1/patrol/records/{rec['record_id']}/media",
    headers=a_headers, files={"file": ("test.jpg", buf2, "image/jpeg")}, data={"kind": "photo"})
print(f"  user100 upload to own record: status={r.status_code} (expect 201)")
assert r.status_code == 201, f"FAIL: user100 cannot upload to own record! body={r.text}"
media = r.json()
print(f"  PASS, media_id={media['media_id']}")

# admin uploads to A's record -> should be 201
buf3 = io.BytesIO()
img.save(buf3, format="JPEG")
buf3.seek(0)
r = requests.post(f"{BASE}/api/v1/patrol/records/{rec['record_id']}/media",
    headers=admin, files={"file": ("test.jpg", buf3, "image/jpeg")}, data={"kind": "photo"})
print(f"  admin upload to user100 record: status={r.status_code} (expect 201)")
assert r.status_code == 201, f"FAIL: admin upload failed! body={r.text}"
print("  PASS")

# cleanup
requests.delete(f"{BASE}/api/v1/patrol/tasks/{t1['task_id']}", headers=admin)
requests.delete(f"{BASE}/api/v1/patrol/tasks/{t2['task_id']}", headers=admin)
print()
print("=== ALL CHECKS PASSED ===")
