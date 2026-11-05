# 证据清单

## 1. 组件

| 项 | 值 |
|---|---|
| 包名 | `com.coloros.regservice` |
| APK | `/product/app/RegService/RegService.apk` |
| 大小 | 5,217,513 bytes |
| SHA-256 | `e0061b2497ba5fcf80a56e7daf88acc025e80274b7023553a816baab581d2010` |
| 版本 | 16.0.1 (160000001)，targetSdk 35 / minSdk 33 |
| 签名 | 系统签名（`pkgFlags=[ SYSTEM HAS_CODE ALLOW_CLEAR_USER_DATA ]`） |

> 出于版权考虑，本仓库**不附带厂商 APK**，仅提供哈希供核验。

## 2. 全部 30 项已授予权限

```
ACCESS_BACKGROUND_LOCATION        ACCESS_COARSE_LOCATION          ACCESS_FINE_LOCATION
ACCESS_NETWORK_STATE              ACCESS_WIFI_STATE               BLUETOOTH_CONNECT
INTERACT_ACROSS_USERS             INTERACT_ACROSS_USERS_FULL      INTERNET
LOCAL_MAC_ADDRESS                 MAINLINE_NETWORK_STACK          MODIFY_PHONE_STATE
MOUNT_UNMOUNT_FILESYSTEMS         PACKAGE_USAGE_STATS             POST_NOTIFICATIONS
QUERY_ALL_PACKAGES                READ_NETWORK_USAGE_HISTORY      READ_PHONE_STATE
READ_PRIVILEGED_PHONE_STATE       RECEIVE_BOOT_COMPLETED          SCHEDULE_EXACT_ALARM
USE_EXACT_ALARM                   WRITE_APN_SETTINGS              WRITE_MEDIA_STORAGE
WRITE_SECURE_SETTINGS             WRITE_SETTINGS                  com.oplus.permission.safe.SECURITY
com.oppo.permission.safe.SECURITY oplus.permission.OPLUS_COMPONENT_SAFE  oppo.permission.OPPO_COMPONENT_SAFE
```

采集来源：`dumpsys package com.coloros.regservice | grep "granted=true"`，共 30 条，无一条由用户手动授予。

## 3. 数据库

路径：`/data/data/com.coloros.regservice/databases/cmcc_dm.db`（SQLite，WAL/journal 模式）

快照哈希：

| 文件 | 时点 | SHA-256 |
|---|---|---|
| `cmcc_dm.db` | 2026-11-06 03:25（上报前） | `43c1e81368ca0a2c317b2f16e2f26a379ae4c789363c60c39612155c1870930f` |
| `dm_new.db` | 2026-11-06 03:39（上报后） | `a75f03f58449e792a4e5b0ef729f3767074551cd682799d76df9bc4bd073f58e` |
| `cmcc_dm_final.db` | 2026-11-06 03:44（处置前最后快照） | `e8f290c48ac1700d2e1a7d35a42323ea19237050d818319b4b466bcf5ea319b4` |

> **原始库不随仓库发布**（内含本人应用清单、周边 Wi-Fi 等个人信息）。结构性证据见 [`db_schema.txt`](db_schema.txt)，可按 `scripts/inspect_db.py` 在自有设备复现。

## 4. 上报配置

`shared_prefs/config_dm.xml`，SHA-256 `1bc04d947f84a5b31dbf12aa6474c4bf59887743ad2c9fb8c44d332f6c0ae6d2`

关键项：

```
APP_REPORT_SWITCH=Y                      key_pre_installed_report_switch=Y
key_wifi_list_report_switch=Y            key_network_report_switch=Y
KEY_TIME_RELATED_TRAFFIC_SWITCH=Y        key_net_speed=Y
key_roaming_report_switch=Y              key_battery_charging_report_switch=Y
key_base_config_url=https://a.fxltsbl.com
key_base_accept_url=https://a.fxltsbl.com
```

## 5. 抓包

`tcpdump -i any -n -s0 -X "host 117.134.71.39"`，摘录见 [`tls_alert_excerpt.txt`](tls_alert_excerpt.txt)

关键帧（未登录网关环境下）：

```
Out IP <local>.xxxxx > 117.134.71.39.443: Flags [P.], length 7
  1503 0300 0202 2e          # TLS Alert: fatal, certificate_unknown(46)
```

登录网关后重测，同一组连接正常完成握手并返回成功（组件日志 `result:1`）。

## 6. 待补充

- [ ] 设置界面中无该组件入口的截图
- [ ] `pm list packages` 处置前后对比
- [ ] 组件日志中 5 条 `result:1` 的原始行（logcat 缓冲已滚动，需复现时重采）
