# ColorOS 运营商 DM 组件遥测分析（`com.coloros.regservice`）

> 一台国行 OnePlus（ColorOS 16 / Android 16）上预装的运营商设备管理组件，被实测确认在后台采集应用清单、Wi-Fi 扫描、基站与 SIM 标识、分应用流量，并周期性上报至第三方域名 `a.fxltsbl.com`。
>
> **TL;DR** — 该组件无界面、无开关、开机自启；30 项权限全部默认授予（含 `READ_PRIVILEGED_PHONE_STATE`、`QUERY_ALL_PACKAGES`、`PACKAGE_USAGE_STATS`、`ACCESS_BACKGROUND_LOCATION`）；本地 SQLite 库 `cmcc_dm.db` 实测存有 458 条应用记录与 2225 条预装清单；上报成功后**立即清空本地表**；上报地址未出现在 OPPO 隐私政策的第三方共享条款中。

---

## 1. 背景

2026 年 10 月底，社区披露了小米 HyperOS 上 `com.mobiletools.systemhelper`（联通 SystemHelper）与 `com.miui.guardprovider`（AiGuard）的数据采集问题（[审计报告](https://github.com/Liu8Can/HyperOS-Security-Analysis)、[技术核验](https://gist.github.com/std-microblock/c38cacab22bf0fffb94b247e09a4d948)）。

本报告记录的是**同一类组件在 ColorOS 上的实现**：包名不同、域名不同，采集字段高度重合。

## 2. 测试环境

| 项 | 值 |
|---|---|
| 设备 | OnePlus PJA110 |
| 系统 | ColorOS 16.0.2.400(CN01)，Android 16 |
| 构建 | `BP2A.250605.015` |
| Root | KernelSU（仅用于读取 `/data/data` 与抓包） |
| 网络 | 校园 Wi-Fi（Dr.Com 认证网关），后登录联网复测 |

## 3. 组件信息

```
package    com.coloros.regservice
APK        /product/app/RegService/RegService.apk   (5,217,513 bytes)
version    16.0.1  (versionCode 160000001)
targetSdk  35      minSdk 33
flags      [ SYSTEM HAS_CODE ALLOW_CLEAR_USER_DATA ]
signature  系统签名
launcher   无（LAUNCHER 计数 = 0）
形态       仅 Service + BroadcastReceiver + ContentProvider
```

厂商适配痕迹：`/system_ext/oplus/sys_deviceidle_whitelist.xml`、`Athena.apk` 的 `appmem_config` 与 `SysProxy` 名单均包含该类组件（同名单还有 `com.mobiletools.systemhelper`、`com.chinaunicom.registerhelper`）。

## 4. 权限（30 项，全部 `GRANTED_BY_DEFAULT`）

| 权限 | 能力 |
|---|---|
| `READ_PRIVILEGED_PHONE_STATE` | IMEI / IMSI / ICCID |
| `QUERY_ALL_PACKAGES` | 全量已安装应用 |
| `PACKAGE_USAGE_STATS` | 启动次数、使用时长 |
| `ACCESS_BACKGROUND_LOCATION` | 后台定位 |
| `READ_NETWORK_USAGE_HISTORY` | 流量历史 |
| `LOCAL_MAC_ADDRESS` | 本机 Wi-Fi MAC |
| `INTERACT_ACROSS_USERS(_FULL)` | 跨用户访问 |
| `WRITE_SECURE_SETTINGS` | 修改安全设置 |

完整列表见 [`docs/evidence.md`](docs/evidence.md)。

## 5. 采集的数据

本地库：`/data/data/com.coloros.regservice/databases/cmcc_dm.db`

| 表 | 行数 | 内容 |
|---|---|---|
| `app_info_*` | **458** | 包名、应用名、安装时间、启动次数、前台时长、移动/Wi-Fi 收发字节 |
| `table_name_preinstall` | **2225** | 预装应用 + 签名 MD5 |
| `table_name_wifi_list` | 1 行 / **21 个热点** | SSID、BSSID、RSSI |
| `table_name_network` | 1 | BSSID、SSID、cellid/lac/pci、band、RSRP/SINR |
| `table_of_time_related_traffic` | **16** | 按小时流量、ICCID/IMSI（密文）、路由器 IP |
| `table_name_battery_charge` / `_bluetooth` / `_lock_info` | 0 | 具备采集能力，当前为空 |

关键观察：**未启动过的应用（`_launchCount = 0`）同样在列**——仅“安装”这一行为即被记录。

## 6. 上报行为

组件通过 `cn.richinfo.dmyk.action.{REGISITER,HEARTBEAT,APPINFO}` 广播触发采集与上报。实测端点（组件自身日志原文）：

```
https://a.fxltsbl.com/TerminalConfigService/terminalConf***   配置下发
https://a.fxltsbl.com/accept/network                          网络/基站
https://a.fxltsbl.com/accept/wifiInfo                         Wi-Fi 扫描
https://a.fxltsbl.com/accept/netSpeedInfo                     网速
https://a.fxltsbl.com/accept/flowCollectService               流量
```

复测结果：上述 5 类任务全部返回 `{"status":"report","result":1}`（成功），**随后本地对应表被清空**（流量 16→0、Wi-Fi 1→0、网络 1→0、网速 1→0）。

传输特征：TLS 1.2，SNI `a.fxltsbl.com`，ALPN `http/1.1`；请求体在发送前经 AES 加密（`cn.richinfo.dm.net.encyptrequest.EncryptJsonRequest` + `libaes-jni.so`）。

> 注：在未认证的网关环境下，客户端因证书校验失败发送 `TLS Alert 0x2e (certificate_unknown)` 并中止 —— 说明其使用系统 CA 严格校验，非明文 HTTP。

## 7. 配置开关

`shared_prefs/config_dm.xml` 中与采集相关的开关全部为 `Y`：

`APP_REPORT_SWITCH`、`key_pre_installed_report_switch`、`key_wifi_list_report_switch`、`key_network_report_switch`、`KEY_TIME_RELATED_TRAFFIC_SWITCH`、`key_net_speed`、`key_roaming_report_switch`、`key_battery_charging_report_switch`

上报地址：`key_base_config_url` / `key_base_accept_url` = `https://a.fxltsbl.com`

## 8. 与隐私政策的偏差

检索 [OPPO 隐私政策原文](https://www.oppo.com/content/dam/oppo/event-page-asset/imagine-if/works-center/v1/assets/privacy-cn.pdf)（36 页）全文：

| 检索词 | 命中 |
|---|---|
| `fxltsbl` / `richinfo` / `彩讯` / `regservice` | 0 |
| `设备管理` | 0 |
| `接收方名称和联系方式` | 0 |

政策中“应用列表”仅出现在“个性化推荐/广告”与“应用使用信息”语境；关于第三方共享只有概括表述（“合作伙伴、服务提供商”）。而《个人信息保护法》第 23 条要求告知**接收方名称与联系方式**并取得**单独同意**。

## 9. 自查与处置

```bash
# 是否存在
adb shell pm list packages | grep regservice
adb shell dumpsys package com.coloros.regservice | grep -m1 "User 0"

# 只读查看数据库（需 root）
adb shell su -c 'cp /data/data/com.coloros.regservice/databases/cmcc_dm.db /sdcard/Download/'
python3 scripts/inspect_db.py cmcc_dm.db

# 卸载（当前用户）
adb shell pm uninstall --user 0 com.coloros.regservice
adb shell pm uninstall --user 0 com.oppo.ctautoregist

# 恢复
adb shell cmd package install-existing com.coloros.regservice
```

## 10. 局限

- 单台设备、单次系统版本，结论不可外推到所有 ColorOS 机型；
- 未做 MITM 解密，请求体内容为推断（依据本地库结构与加密类名）；
- `a.fxltsbl.com` 的运营主体未核实，本报告只陈述“配置指向该域名”；
- 上报成功以组件自身日志的 `result:1` 与本地表清空为准，未在服务端侧验证。

## 11. 参考

- HyperOS 安全审计：<https://github.com/Liu8Can/HyperOS-Security-Analysis>
- 技术核验（含辟谣）：<https://gist.github.com/std-microblock/c38cacab22bf0fffb94b247e09a4d948>
- OPPO 隐私政策：<https://www.oppo.com/content/dam/oppo/event-page-asset/imagine-if/works-center/v1/assets/privacy-cn.pdf>

## 免责声明

本项目仅用于个人信息保护研究与公众知情，不含任何攻击性内容。所有数据来自本人自有设备，未获取他人数据。厂商名称与包名仅用于事实指认。

## License

文本 CC BY-SA 4.0；脚本 MIT。
