# QR Code Style Examples

See below to see what each combination might look like

Start by running `make examples` 

Note: Each section uses a different colour pair from `colour-pairs.json` -- fill colour as background, foreground colour as dots/corners.

All commands pipe through `jq` to decode the return payload and image on completion. 

---

## Mime/Image Format support

| Format  | --format value | Notes                         |
|---------|----------------|-------------------------------|
| PNG     | `png`          | default                       |
| JPEG    | `jpg` or `jpeg`|                               |
| WebP    | `webp`         |                               |
| SVG     | `svg`          | vector, no canvas needed      |
| dataUri | `n/a`          | inline base64                 |

---

## Part 1: Passing Individual CLI flags

<details>
<summary>
&nbsp;&nbsp;&nbsp; QR code dotsOptions -- all 6 types
</summary>

<table><tr>
<td><img src="assets/images/daveco/dots-square.png" width="160"/><br><sub>square</sub></td>
<td><img src="assets/images/daveco/dots-rounded.png" width="160"/><br><sub>rounded</sub></td>
<td><img src="assets/images/daveco/dots-dots.png" width="160"/><br><sub>dots</sub></td>
</tr><tr>
<td><img src="assets/images/daveco/dots-classy.png" width="160"/><br><sub>classy</sub></td>
<td><img src="assets/images/daveco/dots-classy-rounded.png" width="160"/><br><sub>classy-rounded</sub></td>
<td><img src="assets/images/daveco/dots-extra-rounded.png" width="160"/><br><sub>extra-rounded</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# dots type: square (default)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=square \
  --dotsOptions.color="#2B4D00" \
  --backgroundOptions.color="#D4F299" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-square.png

# dots type: rounded
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded \
  --dotsOptions.color="#2B4D00" \
  --backgroundOptions.color="#D4F299" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-rounded.png

# dots type: dots
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=dots \
  --dotsOptions.color="#2B4D00" \
  --backgroundOptions.color="#D4F299" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-dots.png

# dots type: classy
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=classy \
  --dotsOptions.color="#2B4D00" \
  --backgroundOptions.color="#D4F299" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-classy.png

# dots type: classy-rounded
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=classy-rounded \
  --dotsOptions.color="#2B4D00" \
  --backgroundOptions.color="#D4F299" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-classy-rounded.png

# dots type: extra-rounded
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=extra-rounded \
  --dotsOptions.color="#2B4D00" \
  --backgroundOptions.color="#D4F299" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-extra-rounded.png
```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; cornersSquareOptions -- all 3 types
</summary>

<table><tr>
<td><img src="assets/images/daveco/corners-square.png" width="160"/><br><sub>square</sub></td>
<td><img src="assets/images/daveco/corners-dot.png" width="160"/><br><sub>dot</sub></td>
<td><img src="assets/images/daveco/corners-extra-rounded.png" width="160"/><br><sub>extra-rounded</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# corners type: square (default)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#064E3B" \
  --cornersSquareOptions.type=square \
  --cornersSquareOptions.color="#064E3B" \
  --backgroundOptions.color="#A7F3D0" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corners-square.png

# corners type: dot
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#064E3B" \
  --cornersSquareOptions.type=dot \
  --cornersSquareOptions.color="#064E3B" \
  --backgroundOptions.color="#A7F3D0" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corners-dot.png

# corners type: extra-rounded
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#064E3B" \
  --cornersSquareOptions.type=extra-rounded \
  --cornersSquareOptions.color="#064E3B" \
  --backgroundOptions.color="#A7F3D0" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corners-extra-rounded.png

```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; cornersDotOptions -- all 2 types
</summary>

<table><tr>
<td><img src="assets/images/daveco/corner-dot-square.png" width="160"/><br><sub>square</sub></td>
<td><img src="assets/images/daveco/corner-dot-dot.png" width="160"/><br><sub>dot</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# corner dot type: square
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#5C3A00" \
  --cornersSquareOptions.type=extra-rounded --cornersSquareOptions.color="#5C3A00" \
  --cornersDotOptions.type=square \
  --cornersDotOptions.color="#5C3A00" \
  --backgroundOptions.color="#FDE68A" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corner-dot-square.png

# corner dot type: dot
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#5C3A00" \
  --cornersSquareOptions.type=extra-rounded --cornersSquareOptions.color="#5C3A00" \
  --cornersDotOptions.type=dot \
  --cornersDotOptions.color="#5C3A00" \
  --backgroundOptions.color="#FDE68A" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corner-dot-dot.png
```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; qrOptions -- all 4 error correction levels
</summary>

<table><tr>
<td><img src="assets/images/daveco/ecl-L.png" width="160"/><br><sub>L (~7%)</sub></td>
<td><img src="assets/images/daveco/ecl-M.png" width="160"/><br><sub>M (~15%)</sub></td>
<td><img src="assets/images/daveco/ecl-Q.png" width="160"/><br><sub>Q (~25%)</sub></td>
</tr><tr>
<td><img src="assets/images/daveco/ecl-H.png" width="160"/><br><sub>H (~30%)</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# errorCorrectionLevel: L (~7% recovery)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#3B3100" \
  --backgroundOptions.color="#FFF3C4" \
  --qrOptions.errorCorrectionLevel=L \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-L.png

# errorCorrectionLevel: M (~15% recovery)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#3B3100" \
  --backgroundOptions.color="#FFF3C4" \
  --qrOptions.errorCorrectionLevel=M \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-M.png

# errorCorrectionLevel: Q (~25% recovery, library default)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#3B3100" \
  --backgroundOptions.color="#FFF3C4" \
  --qrOptions.errorCorrectionLevel=Q \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-Q.png

# errorCorrectionLevel: H (~30% recovery, use when adding centre image)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#3B3100" \
  --backgroundOptions.color="#FFF3C4" \
  --qrOptions.errorCorrectionLevel=H \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-H.png
```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; Output all image formats 
</summary>

<table><tr>
<td><img src="assets/images/daveco/qr.png" width="160"/><br><sub>PNG</sub></td>
<td><img src="assets/images/daveco/qr.jpg" width="160"/><br><sub>JPEG</sub></td>
<td><img src="assets/images/daveco/qr.webp" width="160"/><br><sub>WebP</sub></td>
</tr><tr>
<td><img src="assets/images/daveco/qr.svg" width="160"/><br><sub>SVG</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# PNG
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#993C1D" \
  --backgroundOptions.color="#FAECE7" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.png

# JPEG
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=jpg \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#993C1D" \
  --backgroundOptions.color="#FAECE7" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.jpg

# WebP
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=webp \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#993C1D" \
  --backgroundOptions.color="#FAECE7" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.webp

# SVG (vector)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=svg \
  --project=daveco \
  --border=10 \
  --margin=10 \
  --dotsOptions.type=rounded --dotsOptions.color="#993C1D" \
  --backgroundOptions.color="#FAECE7" \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.svg

# data URI (extract from JSON field)
docker run --rm qr-cli:latest \
  --data="https://example.com" --format=webp \
  --project=daveco \
  --border=10 \
  --margin=40 \
  --dotsOptions.type=rounded --dotsOptions.color="#993C1D" \
  --backgroundOptions.color="#FAECE7" \
  | jq -r '.image.dataUri'

```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; With margin and custom size
</summary>

<table><tr>
<td><img src="assets/images/daveco/qr.custom.png" width="160"/><br><sub>600x600, margin 20</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

docker run --rm qr-cli:latest \
  --data="https://example.com" --format=png \
  --project=daveco \
  --border=10 \
  --width=600 --height=600 --margin=20 \
  --dotsOptions.type=extra-rounded --dotsOptions.color="#4A1B0C" \
  --backgroundOptions.color="#F5C4B3" \
  --cornersSquareOptions.type=extra-rounded --cornersSquareOptions.color="#4A1B0C" \
  --cornersDotOptions.type=dot --cornersDotOptions.color="#4A1B0C" \
  --qrOptions.errorCorrectionLevel=H \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.custom.png
```
</details>

---

## Part 2: Passing a Full JSON config blob (--json)


<details>
<summary>
&nbsp;&nbsp;&nbsp; Fully-loaded example (multiple options combined) - json
</summary>

<table><tr>
<td><img src="assets/images/daveco/qr.all.logo.png" width="160"/><br><sub>PNG (Facebook logo)</sub></td>
<td><img src="assets/images/daveco/qr.all.logo.jpg" width="160"/><br><sub>JPEG (avatar logo)</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

docker run --rm qr-cli:latest \
  --json='{
    "data": "https://facebook.com",
    "width": 600,
    "height": 600,
    "margin": 20,
    "format": "png",
    "project": "daveco",
    "border": 10,
    "image": "https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg",
    "imageOptions": {
      "crossOrigin": "anonymous",
      "margin": 10
    },
    "qrOptions": {
      "errorCorrectionLevel": "H"
    },
    "dotsOptions": {
      "type": "extra-rounded",
      "color": "#185FA5"
    },
    "backgroundOptions": {
      "color": "#E6F1FB"
    },
    "cornersSquareOptions": {
      "type": "extra-rounded",
      "color": "#185FA5"
    },
    "cornersDotOptions": {
      "type": "dot",
      "color": "#185FA5"
    }
  }' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.all.logo.png

docker run --rm qr-cli:latest \
  --json='{
    "data": "https://browserleaks.com/geo",
    "width": 600,
    "height": 600,
    "margin": 20,
    "format": "jpg",
    "project": "daveco",
    "border": 10,
    "image": "https://i.imgur.com/IKGBe9H.png",
    "imageOptions": {
      "crossOrigin": "anonymous",
      "margin": 10
    },
    "qrOptions": {
      "errorCorrectionLevel": "Q"
    },
    "dotsOptions": {
      "type": "extra-rounded",
      "color": "#185FA5"
    },
    "backgroundOptions": {
      "color": "#E6F1FB"
    },
    "cornersSquareOptions": {
      "type": "extra-rounded",
      "color": "#185FA5"
    },
    "cornersDotOptions": {
      "type": "dot",
      "color": "#185FA5"
    }
  }' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.all.logo.jpg
```

</details>


<details>
<summary>
&nbsp;&nbsp;&nbsp; dotsOptions -- all 6 types - json
</summary>

<table><tr>
<td><img src="assets/images/daveco/dots-square.json.png" width="160"/><br><sub>square</sub></td>
<td><img src="assets/images/daveco/dots-rounded.json.png" width="160"/><br><sub>rounded</sub></td>
<td><img src="assets/images/daveco/dots-dots.json.png" width="160"/><br><sub>dots</sub></td>
</tr><tr>
<td><img src="assets/images/daveco/dots-classy.json.png" width="160"/><br><sub>classy</sub></td>
<td><img src="assets/images/daveco/dots-classy-rounded.json.png" width="160"/><br><sub>classy-rounded</sub></td>
<td><img src="assets/images/daveco/dots-extra-rounded.json.png" width="160"/><br><sub>extra-rounded</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# dots type: square
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#042C53","type":"square"},"backgroundOptions":{"color":"#B5D4F4"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-square.json.png

# dots type: rounded
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#042C53","type":"rounded"},"backgroundOptions":{"color":"#B5D4F4"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-rounded.json.png

# dots type: dots
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#042C53","type":"dots"},"backgroundOptions":{"color":"#B5D4F4"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-dots.json.png

# dots type: classy
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#042C53","type":"classy"},"backgroundOptions":{"color":"#B5D4F4"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-classy.json.png

# dots type: classy-rounded
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#042C53","type":"classy-rounded"},"backgroundOptions":{"color":"#B5D4F4"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-classy-rounded.json.png

# dots type: extra-rounded
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#042C53","type":"extra-rounded"},"backgroundOptions":{"color":"#B5D4F4"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/dots-extra-rounded.json.png
```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; cornersSquareOptions -- all 3 types - json
</summary>

<table><tr>
<td><img src="assets/images/daveco/corners-square.json.png" width="160"/><br><sub>square</sub></td>
<td><img src="assets/images/daveco/corners-dot.json.png" width="160"/><br><sub>dot</sub></td>
<td><img src="assets/images/daveco/corners-extra-rounded.json.png" width="160"/><br><sub>extra-rounded</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# corners type: square
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#1772FD","type":"rounded"},"cornersSquareOptions":{"color":"#1772FD","type":"square"},"backgroundOptions":{"color":"#F9DB65"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corners-square.json.png

# corners type: dot
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#1772FD","type":"rounded"},"cornersSquareOptions":{"color":"#1772FD","type":"dot"},"backgroundOptions":{"color":"#F9DB65"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corners-dot.json.png

# corners type: extra-rounded
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#1772FD","type":"rounded"},"cornersSquareOptions":{"color":"#1772FD","type":"extra-rounded"},"backgroundOptions":{"color":"#F9DB65"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corners-extra-rounded.json.png
```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; cornersDotOptions -- all 2 types - json
</summary>

<table><tr>
<td><img src="assets/images/daveco/corner-dot-square.json.png" width="160"/><br><sub>square</sub></td>
<td><img src="assets/images/daveco/corner-dot-dot.json.png" width="160"/><br><sub>dot</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# corner dot type: square
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#00695C","type":"rounded"},"cornersSquareOptions":{"color":"#00695C","type":"extra-rounded"},"cornersDotOptions":{"color":"#00695C","type":"square"},"backgroundOptions":{"color":"#E0F2F1"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corner-dot-square.json.png

# corner dot type: dot
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#00695C","type":"rounded"},"cornersSquareOptions":{"color":"#00695C","type":"extra-rounded"},"cornersDotOptions":{"color":"#00695C","type":"dot"},"backgroundOptions":{"color":"#E0F2F1"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/corner-dot-dot.json.png
```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; qrOptions -- all 4 error correction levels - json
</summary>

<table><tr>
<td><img src="assets/images/daveco/ecl-L.json.webp" width="160"/><br><sub>L (~7%)</sub></td>
<td><img src="assets/images/daveco/ecl-M.json.webp" width="160"/><br><sub>M (~15%)</sub></td>
<td><img src="assets/images/daveco/ecl-Q.json.webp" width="160"/><br><sub>Q (~25%)</sub></td>
</tr><tr>
<td><img src="assets/images/daveco/ecl-H.json.webp" width="160"/><br><sub>H (~30%)</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# errorCorrectionLevel: L
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"webp","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#4527A0","type":"rounded"},"backgroundOptions":{"color":"#EDE7F6"},"qrOptions":{"errorCorrectionLevel":"L"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-L.json.webp

# errorCorrectionLevel: M
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"webp","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#4527A0","type":"rounded"},"backgroundOptions":{"color":"#EDE7F6"},"qrOptions":{"errorCorrectionLevel":"M"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-M.json.webp

# errorCorrectionLevel: Q (library default)
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"webp","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#4527A0","type":"rounded"},"backgroundOptions":{"color":"#EDE7F6"},"qrOptions":{"errorCorrectionLevel":"Q"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-Q.json.webp

# errorCorrectionLevel: H (best for centre image overlays)
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"webp","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#4527A0","type":"rounded"},"backgroundOptions":{"color":"#EDE7F6"},"qrOptions":{"errorCorrectionLevel":"H"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/ecl-H.json.webp

```

</details>

<details>
<summary>
&nbsp;&nbsp;&nbsp; Output all formats via JSON - json
</summary>

<table><tr>
<td><img src="assets/images/daveco/qr.json.png" width="160"/><br><sub>PNG</sub></td>
<td><img src="assets/images/daveco/qr.json.jpg" width="160"/><br><sub>JPEG</sub></td>
<td><img src="assets/images/daveco/qr.instagram.json.webp" width="160"/><br><sub>WebP (Instagram)</sub></td>
</tr><tr>
<td><img src="assets/images/daveco/qr.json.svg" width="160"/><br><sub>SVG</sub></td>
</tr></table>

```bash
mkdir -p images/daveco

# PNG
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#F57F17","type":"rounded"},"backgroundOptions":{"color":"#FFF8E1"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.json.png

# JPEG
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"jpg","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#F57F17","type":"rounded"},"backgroundOptions":{"color":"#FFF8E1"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.json.jpg

# WebP
docker run --rm qr-cli:latest \
  --json='{"data":"instagram://david.kierans","width":400,"height":400,"format":"webp","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#F57F17","type":"rounded"},"backgroundOptions":{"color":"#FFF8E1"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.instagram.json.webp

# SVG
docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"svg","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#F57F17","type":"rounded"},"backgroundOptions":{"color":"#FFF8E1"}}' \
  | jq -r '.image.base64' | base64 -d > assets/images/daveco/qr.json.svg

# data URI (no decode step needed -- use the field directly)
false && docker run --rm qr-cli:latest \
  --json='{"data":"https://example.com","width":400,"height":400,"format":"png","project":"daveco","border":10,"margin":20,"dotsOptions":{"color":"#F57F17","type":"rounded"},"backgroundOptions":{"color":"#FFF8E1"}}' \
  | jq -r '.image.dataUri'
```

</details>



---

## Option reference summary

| Option key                          | Values                                                     |
|-------------------------------------|------------------------------------------------------------|
| format                              | `png` `jpg` `jpeg` `webp` `svg`                            |
| project                             | any string (used as output filename base)                  |
| border                              | number (pixels added around QR code)                       |
| qrOptions.errorCorrectionLevel      | `L` `M` `Q` (default) `H`                                 |
| dotsOptions.type                    | `square` (default) `rounded` `dots` `classy` `classy-rounded` `extra-rounded` |
| cornersSquareOptions.type           | `square` `dot` `extra-rounded`                             |
| cornersDotOptions.type              | `square` `dot`                                             |
| backgroundOptions.color             | any hex colour string                                      |
| dotsOptions.color                   | any hex colour string                                      |
| width / height                      | number (default 300)                                       |
| margin                              | number (default 0)                                         |
| image                               | optional url of a logo to place in the middle              |

## Full option list
[All Options](https://github.com/oblakstudio/qr-code-styling#qrcodestyling-instance)

[Extra Styling Options](https://github.com/oblakstudio/qr-code-styling#qrcodestyling-methods)


<!--
jq 'walk(if type == "string" and length > 33 then .[0:33] + "..." else . end)'
-->
