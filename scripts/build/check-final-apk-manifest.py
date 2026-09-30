#!/usr/bin/env python3
"""Verify security-sensitive facts in the final merged Android TV APK manifest."""

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID + "}"

FORBIDDEN_PERMISSIONS = {
    "android.permission.BIND_VPN_SERVICE",
    "android.permission.READ_PHONE_STATE",
    "android.permission.RECEIVE_BOOT_COMPLETED",
    "android.permission.REQUEST_INSTALL_PACKAGES",
}
XRAY_SERVICE = "com.fingmi.xray.service.XrayService"


def analyze_manifest(xml_text: str):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise ValueError(f"apkanalyzer returned invalid manifest XML: {error}") from error

    permissions = set()
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag.startswith("uses-permission"):
            name = element.get(A + "name")
            if name:
                permissions.add(name)

    forbidden = sorted(FORBIDDEN_PERMISSIONS & permissions)
    if forbidden:
        raise ValueError("forbidden final APK permissions: " + ", ".join(forbidden))

    application = root.find("application")
    if application is None:
        raise ValueError("final APK manifest has no application element")

    boot_receivers = []
    xray_services = []
    vpn_services = []
    for receiver in application.findall("receiver"):
        name = receiver.get(A + "name", "")
        if name.endswith(".BootReceiver") or name == "BootReceiver":
            boot_receivers.append(name)

    for service in application.findall("service"):
        name = service.get(A + "name", "")
        permission = service.get(A + "permission", "")
        if name == XRAY_SERVICE:
            xray_services.append(service)
        if permission == "android.permission.BIND_VPN_SERVICE":
            vpn_services.append(name)

    if boot_receivers:
        raise ValueError("BootReceiver leaked into final APK manifest: " + ", ".join(boot_receivers))
    if vpn_services:
        raise ValueError("VPN service permission leaked into final APK manifest: " + ", ".join(vpn_services))
    if len(xray_services) != 1:
        raise ValueError(f"expected exactly one {XRAY_SERVICE}, found {len(xray_services)}")

    xray = xray_services[0]
    if xray.get(A + "exported") != "false":
        raise ValueError("XrayService must remain android:exported=false")
    if xray.get(A + "process") != ":xray":
        raise ValueError("XrayService must remain in android:process=:xray")

    return {
        "permissions": sorted(permissions),
        "xray_service": XRAY_SERVICE,
        "xray_exported": xray.get(A + "exported"),
        "xray_process": xray.get(A + "process"),
    }


def self_test():
    good = f"""<manifest xmlns:android="{ANDROID}" package="com.fongmi.android.tv">
      <uses-permission android:name="android.permission.INTERNET"/>
      <application>
        <receiver android:name="com.fongmi.android.tv.receiver.ActionReceiver" android:exported="false"/>
        <service android:name="{XRAY_SERVICE}" android:exported="false" android:process=":xray"/>
      </application>
    </manifest>"""
    result = analyze_manifest(good)
    if result["xray_process"] != ":xray":
        raise AssertionError("valid manifest was not accepted")

    bad_permission = good.replace(
        '<uses-permission android:name="android.permission.INTERNET"/>',
        '<uses-permission android:name="android.permission.READ_PHONE_STATE"/>',
    )
    try:
        analyze_manifest(bad_permission)
    except ValueError as error:
        if "READ_PHONE_STATE" not in str(error):
            raise
    else:
        raise AssertionError("forbidden permission was not rejected")

    bad_receiver = good.replace(
        "com.fongmi.android.tv.receiver.ActionReceiver",
        "com.fongmi.android.tv.receiver.BootReceiver",
    )
    try:
        analyze_manifest(bad_receiver)
    except ValueError as error:
        if "BootReceiver" not in str(error):
            raise
    else:
        raise AssertionError("BootReceiver was not rejected")

    bad_xray = good.replace('android:process=":xray"', 'android:process=":wrong"')
    try:
        analyze_manifest(bad_xray)
    except ValueError as error:
        if "android:process" not in str(error):
            raise
    else:
        raise AssertionError("wrong Xray process was not rejected")

    print("PASS final manifest contract self-test")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apkanalyzer", type=Path)
    parser.add_argument("--apk", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        if args.apkanalyzer or args.apk:
            parser.error("--self-test cannot be combined with APK inputs")
        self_test()
        return

    if not args.apkanalyzer or not args.apk:
        parser.error("--apkanalyzer and --apk are required")
    if not args.apkanalyzer.is_file():
        parser.error(f"apkanalyzer is missing: {args.apkanalyzer}")
    if not args.apk.is_file():
        parser.error(f"APK is missing: {args.apk}")

    try:
        xml_text = subprocess.check_output(
            [str(args.apkanalyzer), "manifest", "print", str(args.apk)],
            text=True,
            stderr=subprocess.STDOUT,
        )
        result = analyze_manifest(xml_text)
    except (subprocess.CalledProcessError, OSError, ValueError) as error:
        parser.error(str(error))

    print(
        "PASS final manifest: "
        f"XrayService exported={result['xray_exported']} "
        f"process={result['xray_process']}; "
        f"{len(result['permissions'])} permissions checked"
    )


if __name__ == "__main__":
    main()
