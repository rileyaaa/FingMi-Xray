# Golden v5.6.0-xray.5 armeabi-v7a APK; extracted 2026-10-08.
# APK SHA-256: cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda
# Command: apkanalyzer dex code --class t11 --method 'w(Ljava/lang/String;)Z' <golden-v7.apk>
# URI.getHost() is passed directly to qz3.a(); current removes IPv6 brackets at this boundary.
.method public static w(Ljava/lang/String;)Z
    .registers 6

    .line 1
    const/4 v0, 0x0

    .line 2
    if-eqz p0, :cond_5e

    .line 3
    .line 4
    invoke-virtual {p0}, Ljava/lang/String;->length()I

    .line 5
    .line 6
    .line 7
    move-result v1

    .line 8
    move v2, v0

    .line 9
    :goto_8
    if-ge v2, v1, :cond_5e

    .line 10
    .line 11
    invoke-virtual {p0, v2}, Ljava/lang/String;->codePointAt(I)I

    .line 12
    .line 13
    .line 14
    move-result v3

    .line 15
    invoke-static {v3}, Ljava/lang/Character;->isWhitespace(I)Z

    .line 16
    .line 17
    .line 18
    move-result v4

    .line 19
    if-nez v4, :cond_58

    .line 20
    .line 21
    :try_start_14
    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    .line 22
    .line 23
    .line 24
    move-result-object p0

    .line 25
    invoke-static {p0}, Ljava/net/URI;->create(Ljava/lang/String;)Ljava/net/URI;

    .line 26
    .line 27
    .line 28
    move-result-object p0
    :try_end_1c
    .catch Ljava/lang/IllegalArgumentException; {:try_start_14 .. :try_end_1c} :catch_57

    .line 29
    invoke-virtual {p0}, Ljava/net/URI;->getScheme()Ljava/lang/String;

    .line 30
    .line 31
    .line 32
    move-result-object v1

    .line 33
    invoke-virtual {p0}, Ljava/net/URI;->getHost()Ljava/lang/String;

    .line 34
    .line 35
    .line 36
    move-result-object p0

    .line 37
    if-eqz v1, :cond_57

    .line 38
    .line 39
    if-nez p0, :cond_29

    .line 40
    .line 41
    goto :goto_57

    .line 42
    :cond_29
    sget-object v2, Ljava/util/Locale;->ROOT:Ljava/util/Locale;

    .line 43
    .line 44
    invoke-virtual {v1, v2}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    .line 45
    .line 46
    .line 47
    move-result-object v1

    .line 48
    const-string v2, "http"

    .line 49
    .line 50
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 51
    .line 52
    .line 53
    move-result v2

    .line 54
    if-nez v2, :cond_4f

    .line 55
    .line 56
    const-string v2, "https"

    .line 57
    .line 58
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 59
    .line 60
    .line 61
    move-result v2

    .line 62
    if-nez v2, :cond_4f

    .line 63
    .line 64
    const-string v2, "rtsp"

    .line 65
    .line 66
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 67
    .line 68
    .line 69
    move-result v2

    .line 70
    if-nez v2, :cond_4f

    .line 71
    .line 72
    const-string v2, "rtspt"

    .line 73
    .line 74
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    .line 75
    .line 76
    .line 77
    move-result v1

    .line 78
    if-eqz v1, :cond_57

    .line 79
    .line 80
    :cond_4f
    invoke-static {p0}, Lqz3;->a(Ljava/lang/String;)Z

    .line 81
    .line 82
    .line 83
    move-result p0

    .line 84
    if-nez p0, :cond_57

    .line 85
    .line 86
    const/4 p0, 0x1

    .line 87
    return p0

    .line 88
    :catch_57
    :cond_57
    :goto_57
    return v0

    .line 89
    :cond_58
    invoke-static {v3}, Ljava/lang/Character;->charCount(I)I

    .line 90
    .line 91
    .line 92
    move-result v3

    .line 93
    add-int/2addr v2, v3

    .line 94
    goto :goto_8

    .line 95
    :cond_5e
    return v0
.end method
