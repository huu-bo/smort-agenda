# smort-agenda
python `3.7` (should i upgrade, i have `3.9`)

# *WARNING*
stores login credentials as plain text

# configuration

```json
{
  "background": {
    "scale": false,
    "url": "https://imgae.png"
  }
}
```

## background
### scale
`false` do not scale\
`true` scale to fit\
`"aspect"` scale, keep aspect ratio, center image
### url
if `null`, it doesn't draw a background, same as just not specifying `background`

## lines
defaults to `true`, render week and hour lines on background

## appointment_background
defaults to `true`, fill appointments