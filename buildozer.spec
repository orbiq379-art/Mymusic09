[app]
title = My Music
package.name = mymusic
package.domain = org.mymusic
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,mp3,wav,ogg,m4a,aac,flac
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Android permissions needed to read local music on older Android versions.
android.permissions = READ_EXTERNAL_STORAGE

# Keep the build focused on an installable debug APK.
android.archs = arm64-v8a
android.api = 35
android.minapi = 23

[buildozer]
log_level = 2
warn_on_root = 1
