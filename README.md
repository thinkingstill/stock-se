# stock-se 页面
- `stock_daily`每日股票3D可视化
- `stock_top` 每日股票日历图

# aktools API
## termux安装

      # 1. 安装 proot 环境
      pkg install proot-distro
      
      # 2. 安装 Ubuntu 22.04
      proot-distro install ubuntu
      
      # 3. 安装虚拟环境支持
      sudo apt install python3.12-venv
      
      # 4. 创建并激活虚拟环境
      python3 -m venv ~/aktools_venv
      source ~/aktools_venv/bin/activate
      
      # 5. 安装 aktools（虚拟环境内）
      pip install aktools --no-cache-dir
      
      # 6. 验证安装
      python -m  aktools --version
      python -m  aktools

