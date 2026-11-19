package updater

import (
	"bytes"
	"fmt"
	"log/slog"
	"os/exec"
	"strings"

	"github.com/marcopiovanello/yt-dlp-web-ui/v4/server/config"
)

// UpdateExecutable updates yt-dlp.
//
// Standalone builds update themselves with `yt-dlp -U`. Installs from PyPI
// (which is how the Docker image ships yt-dlp) refuse to self-update and
// print "You installed yt-dlp with pip ...", so for those we upgrade through
// pip instead. The [default] extra is included because it pins yt-dlp-ejs,
// which must match the yt-dlp version.
func UpdateExecutable() error {
	out, err := exec.Command(config.Instance().Paths.DownloaderPath, "-U").CombinedOutput()

	if !strings.Contains(strings.ToLower(string(out)), "with pip") {
		if err != nil {
			return fmt.Errorf("yt-dlp -U failed: %w: %s", err, bytes.TrimSpace(out))
		}
		slog.Info("yt-dlp self-update finished", slog.String("output", string(bytes.TrimSpace(out))))
		return nil
	}

	slog.Info("yt-dlp was installed with pip, updating through pip")

	out, err = exec.Command(
		"python3", "-m", "pip", "install",
		"--no-cache-dir", "--disable-pip-version-check", "--upgrade",
		"yt-dlp[default]",
	).CombinedOutput()
	if err != nil {
		return fmt.Errorf("pip upgrade of yt-dlp failed: %w: %s", err, bytes.TrimSpace(out))
	}

	slog.Info("yt-dlp updated through pip")
	return nil
}
