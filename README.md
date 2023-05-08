
# Geist Watchdog Exporter

The Geist Watchdog Exporter is a Prometheus exporter for collecting metrics from Geist Watchdog environment monitoring devices. This exporter supports Geist Watchdog models 1200 and 100NPS.

## Prerequisites

- Python 3.7 or newer
- Prometheus server

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/GeistWatchdogExporter.git
```

2. Change to the project directory:

```bash
cd GeistWatchdogExporter
```

3. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Configuration

In `collector.py`:

- Update the `sources_1200` and `sources_100NPS` arrays with the addresses of your Geist Watchdog devices.
- Set your authentication credentials in the `auth_username` and `auth_password` variables.
- Update the `base64string` variable with the Base64-encoded string for Basic Authentication required by the 1200 model. You can generate this string using an online converter or CLI tools. Search for \"Basic Authentication Header Generator\" to find suitable tools.

In `start_exporter.sh`:

- Update the path to the directory where you deployed the GeistWatchdogExporter.

## Usage

1. Make sure the `start_exporter.sh` script is executable:

```bash
chmod +x start_exporter.sh
```

2. Run the exporter:

```bash
./start_exporter.sh
```

By default, the exporter will be available at `http://localhost:7000/metrics`.

3. Configure Prometheus to scrape metrics from the exporter. Add the following job to your `prometheus.yml` configuration file:

```yaml
scrape_configs:
  - job_name: 'geist_watchdog'
    static_configs:
      - targets: ['localhost:7000']
```

4. Restart the Prometheus server to apply the changes.

## Disclaimer

This project is provided \"AS-IS\" without warranty of any kind, either express or implied, including but not limited to the implied warranties of merchantability and fitness for a particular purpose. The author(s) and maintainer(s) of this project shall not be held liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption) however caused and on any theory of liability, whether in contract, strict liability, or tort (including negligence or otherwise) arising in any way out of the use of this software, even if advised of the possibility of such damage.
