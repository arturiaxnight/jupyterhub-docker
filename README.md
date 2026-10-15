# JupyterHub + Docker

以 [Docker](https://www.docker.com/) / [Docker Compose](https://docs.docker.com/compose/) 部署的 [JupyterHub](https://jupyter.org/hub)：每位使用者由 [DockerSpawner](https://github.com/jupyterhub/dockerspawner) 啟動獨立的 JupyterLab 容器，適合研究室、教學與醫師／研究人員共用運算資源。

本專案由 Université de Versailles 的舊版部署（CAS 認證、JupyterHub 0.9、Traefik v1）現代化而來。

---

## 功能一覽

| 功能 | 說明 |
|------|------|
| **DockerSpawner** | 每位登入使用者一個隔離的 Lab 容器 |
| **NativeAuthenticator** | 網頁註冊／登入，無需外部 CAS／OAuth |
| **預建管理員帳號** | 由 `.env` 寫入帳密，Hub 啟動時自動建立，不必先 Sign up |
| **註冊需核准** | 一般使用者註冊後需管理員核准才能登入與使用計算資源 |
| **資料持久化** | 每位使用者一個 Docker named volume（`jupyterhub-user-<username>`） |
| **GPU** | 可將主機 NVIDIA GPU 掛入使用者容器（需 nvidia-container-toolkit） |
| **ML／統計環境** | 預裝 PyTorch（CUDA）、TensorFlow（CUDA）、R + IRkernel |
| **暗黑模式** | JupyterLab 預設 `JupyterLab Dark` |
| **資源上限** | 可設定每使用者 CPU／記憶體上限 |
| **閒置回收** | 自動關閉長時間閒置的使用者伺服器 |
| **既有 Docker network** | 預設加入外部網路 `apps`（可改） |
| **可選 HTTPS** | Traefik v3 反向代理（`--profile proxy`） |

---

## 架構

```
瀏覽器
  │
  ├─ http://<主機>:HUB_PORT          （預設 18000）
  └─ 或 Traefik :443                 （--profile proxy）
        │
        ▼
  jupyterhub 容器（Hub + ConfigurableHTTPProxy）
        │
        ├─ /var/run/docker.sock  → 為使用者 spawn Lab 容器
        ├─ jupyterhub_data       → Hub 資料庫／cookie secret
        └─ network: apps         → 與其他服務、使用者容器互通
                │
                ▼
        jupyter-<username> 容器（每人一個）
                ├─ 映像：jupyterhub_lab（PyTorch / TF / R）
                ├─ volume：jupyterhub-user-<username> → /home/jovyan/work
                └─ 可選：NVIDIA GPU
```

---

## 相對舊版的主要調整

- JupyterHub **0.9 → 5.x**（目前預設 `5.2.1`）
- 認證：**大學 CAS → NativeAuthenticator**（自助註冊 + 管理員核准）
- Spawner／映像：改為現代 **DockerSpawner** + 自建 CUDA Lab 映像
- 網路：改接既有外部網路 **`apps`**（不再自建 `jupyterhub-network`）
- 反向代理：Traefik **v1 → v3**，改為 compose profile 選用
- 新增：管理員帳密自動建立、GPU、R／PyTorch／TensorFlow、暗黑主題、閒置回收

---

## 需求

- Docker Engine 20.10+
- Docker Compose v2
- 已存在的 Docker network（預設名稱 `apps`）：

  ```bash
  docker network create apps   # 若尚不存在
  ```

- （選用 GPU）主機已安裝 [NVIDIA Driver](https://www.nvidia.com/drivers/) 與 [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

---

## 快速開始

### 1. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env：管理員帳密、埠號、資源、GPU、網路名稱等
```

### 2. 建置並啟動

```bash
docker compose build
docker compose up -d
```

### 3. 登入

開啟 <http://localhost:18000>（埠號由 `HUB_PORT` 決定）：

1. 使用 `.env` 的 `JUPYTERHUB_ADMIN` / `JUPYTERHUB_ADMIN_PASSWORD` 直接登入  
   （Hub 啟動時會自動建立並核准該管理員，**不必先 Sign up**）
2. 登入後會自動 spawn JupyterLab 容器

---

## 帳號與權限

### 管理員（預建）

| 變數 | 說明 |
|------|------|
| `JUPYTERHUB_ADMIN` | 管理員使用者名稱（預設 `admin`） |
| `JUPYTERHUB_ADMIN_PASSWORD` | 管理員密碼（寫在 `.env`，勿提交 git） |

實作：`jupyterhub/bootstrap_admin.py` 於容器啟動時寫入 NativeAuthenticator 資料庫（bcrypt、已核准）。

### 一般使用者註冊與核准（預設）

`OPEN_SIGNUP=false` 時：

1. 使用者至 `/hub/signup` 註冊  
2. **核准前無法登入，也不能啟動 Lab**  
3. 管理員登入後至 `/hub/authorize`（例如 <http://localhost:18000/hub/authorize>）核准或拒絕  
4. 核准後即可登入並使用計算資源  

相關變數：

| 變數 | 預設 | 說明 |
|------|------|------|
| `OPEN_SIGNUP` | `false` | `false`＝需核准；`true`＝註冊即可登入 |
| `ENABLE_SIGNUP` | `true` | `false`＝關閉註冊表單 |

---

## 使用者環境（Lab 映像）

基底：`quay.io/jupyter/pytorch-notebook:cuda12-latest`  
定義見 [`jupyterlab/Dockerfile`](jupyterlab/Dockerfile)。

### 預裝內容

| 類別 | 內容 |
|------|------|
| **Python** | scipy 棧（numpy、pandas、matplotlib…） |
| **PyTorch** | CUDA 版（基底映像提供） |
| **TensorFlow** | `tensorflow[and-cuda]` |
| **R** | R + IRkernel；Launcher 可開 R Notebook |
| **R 套件** | r-essentials、tidyverse、shiny、rmarkdown、caret、randomforest、survival、survminer、ggplot2、data.table |
| **其他** | git、vim、jupyterlab-git |
| **主題** | 預設 JupyterLab Dark（`jupyterlab/overrides.json`） |

### 自行安裝套件

Notebook 內可使用：

```python
!pip install some-package
```

亦可使用映像內的 `conda` / `mamba` / `pip`。

> 注意：容器停止後會被刪除（`DockerSpawner.remove = True`）。  
> `!pip` 裝在容器內的套件，下次重新啟動伺服器後通常會消失。  
> **會長期保留的只有** `/home/jovyan/work`（對應 Docker volume）。

### 更換／擴充映像

編輯 `jupyterlab/Dockerfile` 後：

```bash
docker compose build jupyterlab
docker compose up -d jupyterhub
# 既有 Lab 需停止後再啟動才會用到新映像
docker stop jupyter-<username>   # 或於 Hub 介面 Stop My Server
```

---

## GPU

| 變數 | 預設 | 說明 |
|------|------|------|
| `ENABLE_GPU` | `true` | 是否將 GPU 掛入使用者容器 |
| `GPU_COUNT` | `-1` | `-1`＝全部 GPU；或指定數量 |

需求：主機 NVIDIA 驅動 + nvidia-container-toolkit（Docker runtime 需含 `nvidia`）。

多位使用者會**共用**同一張（或多張）實體 GPU；顯存不足時可能 OOM，請自行協調負載。

---

## 資源與閒置回收

| 變數 | 預設 | 說明 |
|------|------|------|
| `CPU_LIMIT` | `4` | 每使用者 CPU 上限 |
| `MEM_LIMIT` | `16G` | 每使用者記憶體上限 |
| `CULL_TIMEOUT` | `3600` | 閒置幾秒後回收伺服器（預設 1 小時） |

---

## 資料持久化

| 資料 | 位置 | 說明 |
|------|------|------|
| 使用者 notebook／檔案 | Docker volume `jupyterhub-user-<username>` → 容器內 `/home/jovyan/work` | Lab 左側檔案瀏覽器的 `/` 即此目錄 |
| Hub 資料庫／cookie | volume `jupyterhub_jupyterhub_data` → `/data` | 使用者帳號、授權狀態等 |
| 主機上 volume 路徑（範例） | `/var/lib/docker/volumes/jupyterhub-user-admin/_data` | named volume，非 bind mount |

- `docker compose down`：**不會**刪除上述 volumes  
- `docker volume rm ...` 或 `docker compose down -v`：才會清掉（請小心）

若要改成綁定主機某個資料夾，需調整 `jupyterhub_config.py` 的 `c.DockerSpawner.volumes`。

---

## Docker 網路

預設使用**既有**外部網路 `apps`：

```yaml
networks:
  apps:
    external: true
    name: ${DOCKER_NETWORK_NAME:-apps}
```

| 變數 | 預設 | 說明 |
|------|------|------|
| `DOCKER_NETWORK_NAME` | `apps` | Hub 與使用者 Lab 容器加入的網路名稱 |

---

## 環境變數總表（`.env`）

完整範本見 [`.env.example`](.env.example)。`.env` 已列入 `.gitignore`，請勿把真實密碼提交到 git。

| 變數 | 預設 | 說明 |
|------|------|------|
| `COMPOSE_PROJECT_NAME` | `jupyterhub` | Compose 專案名（影響映像／volume 名稱） |
| `HUB_PORT` | `18000` | 對外埠 |
| `DOCKER_NETWORK_NAME` | `apps` | 外部 Docker network |
| `JUPYTERHUB_ADMIN` | `admin` | 管理員帳號 |
| `JUPYTERHUB_ADMIN_PASSWORD` | （必填） | 管理員密碼 |
| `OPEN_SIGNUP` | `false` | 是否免審核註冊 |
| `ENABLE_SIGNUP` | `true` | 是否開放註冊 |
| `JUPYTERHUB_VERSION` | `5.2.1` | Hub 映像版本 |
| `CPU_LIMIT` | `4` | 每使用者 CPU |
| `MEM_LIMIT` | `16G` | 每使用者記憶體 |
| `ENABLE_GPU` | `true` | 是否啟用 GPU |
| `GPU_COUNT` | `-1` | GPU 數量（`-1`＝全部） |
| `CULL_TIMEOUT` | `3600` | 閒置回收秒數 |
| `PUBLIC_URL` | （空） | 對外 HTTPS URL（走反向代理時設定） |
| `HOST` | `localhost` | Traefik Host 規則 |
| `TLS_CERTS_DIR` | `./reverse-proxy/certs` | TLS 憑證目錄 |

---

## 常用指令

```bash
# 狀態／日誌
docker compose ps
docker compose logs -f jupyterhub

# 重建 Lab 映像並套用
docker compose build jupyterlab
docker compose up -d jupyterhub

# 停止（保留 volumes）
docker compose down

# 重置 Hub 資料庫（帳號／授權；不刪使用者 notebook volumes）
docker compose down
docker volume rm jupyterhub_jupyterhub_data
docker compose up -d
```

---

## HTTPS（選用）

1. 將 `cert.pem`、`key.pem` 放到 `reverse-proxy/certs/`  
2. `.env` 設定 `HOST`（網域）與 `PUBLIC_URL=https://你的網域`  
3. 啟動：

```bash
docker compose --profile proxy up -d
```

- Traefik 設定：[`reverse-proxy/traefik.toml`](reverse-proxy/traefik.toml)  
- Dashboard：<http://localhost:8080>

---

## 目錄說明

| 路徑 | 用途 |
|------|------|
| `docker-compose.yml` | Hub、Lab 建置服務、選用 Traefik |
| `.env` / `.env.example` | 環境變數 |
| `jupyterhub/Dockerfile` | Hub 映像（含 dockerspawner、nativeauthenticator、idle-culler） |
| `jupyterhub/jupyterhub_config.py` | Hub／Spawner／認證／GPU／資源設定 |
| `jupyterhub/bootstrap_admin.py` | 啟動時建立／更新管理員帳密 |
| `jupyterhub/start.sh` | Hub 容器進入點 |
| `jupyterlab/Dockerfile` | 使用者 Lab 映像（PyTorch／TF／R） |
| `jupyterlab/overrides.json` | JupyterLab 預設暗黑主題 |
| `jupyterlab/conda-activate.sh` | notebook 啟動前啟用 conda |
| `reverse-proxy/` | Traefik HTTPS（選用） |

---

## 參考

- [JupyterHub 文件](https://jupyterhub.readthedocs.io/)
- [NativeAuthenticator](https://native-authenticator.readthedocs.io/)
- [DockerSpawner](https://jupyterhub-dockerspawner.readthedocs.io/)
- [官方 Docker 參考部署](https://github.com/jupyterhub/jupyterhub-deploy-docker)
- [Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/)
- [原始部落格說明（舊版 UVSQ 部署）](https://opendreamkit.org/2018/10/17/jupyterhub-docker/)

---

## 授權

MIT（見 [LICENSE](LICENSE)）。部分早期工作曾由 EU H2020 [OpenDreamKit](https://opendreamkit.org/) 資助。
