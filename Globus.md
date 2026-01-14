# HuBMAP Data Download Guide using Globus Connect Personal

This guide documents the process for downloading HuBMAP datasets to specific storage locations using `hubmap-clt` and Globus Connect Personal.

---

## Prerequisites

- Python 3.8 or higher
- Access to storage location (e.g., `/teradata/` NFS mount or home directory)
- Valid HuBMAP/Globus credentials
- Internet connection with appropriate firewall permissions

---

## Setup Instructions

### ✅ 1. Install Atlas Consortia Command Line Tools
```bash
pip install atlas-consortia-clt
```

Or install in a conda environment (recommended):
```bash
conda create -n hra-deepcell python=3.12
conda activate hra-deepcell
pip install atlas-consortia-clt
```

### ✅ 2. Authenticate using Globus CLI
```bash
globus login --no-local-server
```

- Copy the link shown in the terminal
- Open it in your browser
- Complete the authentication
- Authorize Globus access

To verify authentication:
```bash
globus whoami --verbose
```

### ✅ 3. Create `manifest.txt` File

Follow the [HuBMAP Manifest File Documentation](https://docs.hubmapconsortium.org/clt) to create a `manifest.txt` file listing the dataset(s) to download.

**Example manifest format:**
```
HBM953.LMWQ.235 /pipeline_output/expr/reg001_expr.ome.tiff
HBM953.LMWQ.235 /pipelineConfig.json
```

⚠️ **Important:** Ensure there are no comments in the manifest file, as they may cause parsing errors.

### ✅ 4. Install and Configure Globus Connect Personal

Download and extract:
```bash
cd ~
wget https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
tar -xzf globusconnectpersonal-latest.tgz
```

Start Globus Connect Personal for initial setup:
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal -start &
```

Complete the setup as prompted (follow the URL to authenticate). After initial setup, stop it:
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal -stop
```

### ✅ 5. Configure Download Paths

Edit the config-paths file:
```bash
nano ~/.globusonline/lta/config-paths
```

Add your desired download paths:

**For home directory only:**
```
~/,0,1
```

**For specific directories of teradata(e.g., NFS mount):**
```
/teradata/username,0,1
```

**For both home and specific directories:(not recommended)**
```
~/,0,1
/teradata/username/deepcell-experiments-data/intestine-codex-stanford,0,1
/teradata/username/deepcell-experiments-data/spleen-codex-ufl,0,1
```

⚠️ **Critical:** Do NOT include `~/,0,1` if you ONLY want to download to absolute paths like `/teradata/`. Including it may cause files to download to `~/teradata/` instead of `/teradata/`.

Save and exit (Ctrl+X, Y, Enter)

Start Globus with restricted paths:

**For home directory only:**
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal -start -restrict-paths "rw~" &
```

**For specific directories:**
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal \
  -start \
  -restrict-paths "rw/teradata/username/deepcell-experiments-data/intestine-codex-stanford,rw/teradata/username/deepcell-experiments-data/spleen-codex-ufl" &
```

**For both:**
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal \
  -start \
  -restrict-paths "rw~,rw/teradata/username/deepcell-experiments-data/intestine-codex-stanford,rw/teradata/username/deepcell-experiments-data/spleen-codex-ufl" &
```

Verify Globus is running:
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal -status
```

Expected output:
```
Globus Online:   connected
Transfer Status: idle
```

### ✅ 6. Transfer Data using HuBMAP CLI

Activate your conda environment:
```bash
conda activate hra-deepcell
```

Download to default location (home directory):
```bash
hubmap-clt transfer manifest.txt
```

Download to specific directory:
```bash
hubmap-clt transfer manifest.txt -d /teradata/username/deepcell-experiments-data/intestine-codex-stanford
```



## Common Issues and Solutions

### ⚠️ Session Reauthentication Required

**Error:**
```
Session reauthentication required (Globus Transfer)
```

**Fix:**
```bash
globus session update <SESSION-ID>
```
Or:
```bash
globus login --no-local-server
```

### ⚠️ Files Download to Wrong Location

If files download to `~/teradata/` instead of `/teradata/`:

1. Edit config-paths and remove `~/,0,1`:
```bash
nano ~/.globusonline/lta/config-paths
```

2. Restart Globus Connect Personal:
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal -stop
~/globusconnectpersonal-3.2.8/globusconnectpersonal -start -restrict-paths "rw/teradata/username/..." &
```

### ⚠️ SSL Connection Timeout

**Error:**
```
Details: TIMEOUT
SSL connection timeout
```

**Cause:** Firewall or SSL inspection blocking Globus traffic.

**Fix:** Contact your system administrator to:
- Whitelist IP: `192.231.243.138`
- Open ports: 443 (HTTPS) and 50000-51000 (data transfer)
- Configure SSL/TLS inspection bypass for Globus traffic

**Temporary Workaround:** Use the Globus web interface at https://app.globus.org/file-manager

### ⚠️ Marker Metadata Mismatch

**Note:** Markers are extracted from the .ome.tiff metadata and not the pipeline_config.json due to potential size mismatches. Always validate marker information against the OME-TIFF metadata.

### ⚠️ Timeout Error - Globus Service Down

**Error:**
```
Timeout error
Connection timeout
Request timeout
```

**Cause:** The Globus service or HuBMAP data endpoint is temporarily down or unreachable.

**Fix:**
1. Check Globus service status at https://status.globus.org/
2. Verify HuBMAP service status
3. Wait a few minutes and retry the transfer
4. If persistent, check if your local Globus Connect Personal is running:
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal -status
```
5. Try restarting Globus Connect Personal:
```bash
~/globusconnectpersonal-3.2.8/globusconnectpersonal -stop
~/globusconnectpersonal-3.2.8/globusconnectpersonal -start &
```
6. If issues persist, contact HuBMAP support or try again later

### ⚠️ Globus Already Running

**Error:**
```
Another Globus Connect Personal is currently running
```

**Fix:**
```bash
pkill -f globusconnect
sleep 3
~/globusconnectpersonal-3.2.8/globusconnectpersonal -start &
```

### ⚠️ Command Not Found

**Error:**
```
hubmap-clt: command not found
```

**Fix:**
```bash
conda activate hra-deepcell
pip install atlas-consortia-clt
```

---

## Quick Reference
```bash
# Start Globus
~/globusconnectpersonal-3.2.8/globusconnectpersonal -start &

# Stop Globus
~/globusconnectpersonal-3.2.8/globusconnectpersonal -stop

# Check status
~/globusconnectpersonal-3.2.8/globusconnectpersonal -status

# Download data
hubmap-clt transfer manifest.txt -d /path/to/destination

# Monitor transfer
globus task list --limit 5
globus task show TASK_ID
```

---

## Additional Resources

- [HuBMAP CLI Documentation](https://docs.hubmapconsortium.org/clt)
- [Globus Connect Personal Documentation](https://docs.globus.org/how-to/globus-connect-personal-linux/)
- [Globus Firewall Troubleshooting](https://docs.globus.org/globus-connect-server/v5/reference/troubleshooting/#troubleshooting-firewall-issues)
- [HuBMAP Data Portal](https://portal.hubmapconsortium.org/)

---

