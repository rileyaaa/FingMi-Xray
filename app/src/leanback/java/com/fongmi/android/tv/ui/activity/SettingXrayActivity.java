package com.fongmi.android.tv.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;

import androidx.viewbinding.ViewBinding;

import com.fingmi.xray.config.XrayShareLinkNormalizer;
import com.fingmi.xray.service.XrayOperation;
import com.fingmi.xray.session.XraySettingsController;
import com.fingmi.xray.util.XrayErrorSanitizer;
import com.fongmi.android.tv.R;
import com.fongmi.android.tv.databinding.ActivitySettingXrayBinding;
import com.fongmi.android.tv.event.XrayImportEvent;
import com.fongmi.android.tv.event.XrayLiveRulesEvent;
import com.fongmi.android.tv.ui.base.BaseActivity;
import com.fongmi.android.tv.utils.Notify;

import org.greenrobot.eventbus.Subscribe;
import org.greenrobot.eventbus.ThreadMode;

public final class SettingXrayActivity extends BaseActivity
        implements XraySettingsController.Listener {

    private ActivitySettingXrayBinding mBinding;
    private XraySettingsController mXray;
    private long mOperationId = Long.MIN_VALUE;
    private int mOperation = -1;
    private String mTestLink = "";
    private boolean mTestUdp;
    private boolean mTestTlsFragment;

    public static void start(Activity activity) {
        activity.startActivity(new Intent(activity, SettingXrayActivity.class));
    }

    @Override
    protected ViewBinding getBinding() {
        return mBinding = ActivitySettingXrayBinding.inflate(getLayoutInflater());
    }

    @Override
    protected void initView(Bundle savedInstanceState) {
        mXray = new XraySettingsController(this, this);
        mBinding.udpSwitch.setChecked(mXray.isUdpEnabled());
        mBinding.tlsFragmentSwitch.setChecked(mXray.isTlsFragmentEnabled());
        mBinding.liveAutoGroups.setText(mXray.getLiveAutoGroups());
        mBinding.liveAutoChannels.setText(mXray.getLiveAutoChannels());
        try {
            mBinding.link.setText(mXray.getShareLink());
            mBinding.link.setSelection(mBinding.link.length());
        } catch (Exception | LinkageError error) {
            Notify.show(XrayErrorSanitizer.sanitize(error));
        }
        mBinding.link.requestFocus();
    }

    @Override
    protected void initEvent() {
        mBinding.udp.setOnClickListener(this::onUdp);
        mBinding.tlsFragment.setOnClickListener(view -> mBinding.tlsFragmentSwitch.setChecked(
                !mBinding.tlsFragmentSwitch.isChecked()));
        mBinding.save.setOnClickListener(this::onSave);
        mBinding.test.setOnClickListener(this::onTest);
        mBinding.phone.setOnClickListener(this::onPhone);
        mBinding.delete.setOnClickListener(this::onDelete);
    }

    private void onUdp(View view) {
        mBinding.udpSwitch.setChecked(!mBinding.udpSwitch.isChecked());
    }

    private void onSave(View view) {
        if (mOperation == XrayOperation.RESET_SECURITY) return;
        try {
            mXray.save(readLink(), mBinding.udpSwitch.isChecked(),
                    mBinding.tlsFragmentSwitch.isChecked(),
                    mBinding.liveAutoGroups.getText().toString(),
                    mBinding.liveAutoChannels.getText().toString());
            Notify.show(R.string.xray_saved);
        } catch (Exception | LinkageError error) {
            Notify.show(XrayErrorSanitizer.sanitize(error));
        }
    }

    private void onTest(View view) {
        if (mOperationId != Long.MIN_VALUE) return;
        try {
            mTestLink = XrayShareLinkNormalizer.normalize(readLink());
            mTestUdp = mBinding.udpSwitch.isChecked();
            mTestTlsFragment = mBinding.tlsFragmentSwitch.isChecked();
            Notify.progress(getActivity());
            mOperation = XrayOperation.TEST;
            mOperationId = mXray.test(mTestLink, mTestUdp, mTestTlsFragment);
        } catch (Exception | LinkageError error) {
            clearOperation();
            Notify.dismiss();
            Notify.show(XrayErrorSanitizer.sanitize(error));
        }
    }

    private void onPhone(View view) {
        PushActivity.start(this, 6);
    }

    private void onDelete(View view) {
        if (mOperationId != Long.MIN_VALUE) return;
        try {
            Notify.progress(getActivity());
            mOperation = XrayOperation.RESET_SECURITY;
            mOperationId = mXray.delete(() -> {
                mBinding.link.setText("");
                mBinding.udpSwitch.setChecked(false);
                mBinding.tlsFragmentSwitch.setChecked(false);
                mBinding.liveAutoGroups.setText("");
                mBinding.liveAutoChannels.setText("");
            });
        } catch (Exception | LinkageError error) {
            clearOperation();
            Notify.dismiss();
            Notify.show(XrayErrorSanitizer.sanitize(error));
        }
    }

    @Override
    public void onXraySettingsResult(
            long operationId,
            int operation,
            boolean success,
            long latencyMs,
            String message) {
        if (operationId != mOperationId) return;

        int finishedOperation = mOperation;
        clearOperation();
        Notify.dismiss();

        if (finishedOperation == XrayOperation.TEST && !testInputUnchanged()) {
            Notify.show(R.string.xray_changed_retry);
            return;
        }

        if (!success) {
            Notify.show(message);
            return;
        }

        if (finishedOperation == XrayOperation.RESET_SECURITY) {
            Notify.show(R.string.xray_deleted);
        } else if (finishedOperation == XrayOperation.TEST) {
            Notify.show(getString(R.string.xray_test_success, latencyMs));
        }
    }

    private boolean testInputUnchanged() {
        try {
            return XrayShareLinkNormalizer.normalize(readLink()).equals(mTestLink)
                    && mBinding.udpSwitch.isChecked() == mTestUdp
                    && mBinding.tlsFragmentSwitch.isChecked() == mTestTlsFragment;
        } catch (Exception | LinkageError ignored) {
            return false;
        }
    }

    @Subscribe(threadMode = ThreadMode.MAIN)
    public void onXrayImportEvent(XrayImportEvent event) {
        if (event == null || isBlank(event.link())) return;

        if (mOperationId != Long.MIN_VALUE && mOperation != XrayOperation.RESET_SECURITY) {
            mXray.abandon();
            clearOperation();
            Notify.dismiss();
        }

        String link = event.link().trim();
        mBinding.link.setText(link);
        mBinding.link.setSelection(mBinding.link.length());
        Notify.show(R.string.xray_phone_received);
    }

    @Subscribe(threadMode = ThreadMode.MAIN)
    public void onXrayLiveRulesEvent(XrayLiveRulesEvent event) {
        if (event == null || mOperation == XrayOperation.RESET_SECURITY) return;
        mBinding.liveAutoGroups.setText(event.groups());
        mBinding.liveAutoChannels.setText(event.channels());
        Notify.show(R.string.xray_live_rules_received);
    }

    private static boolean isBlank(String value) {
        if (value == null) return true;
        for (int offset = 0; offset < value.length();) {
            int codePoint = value.codePointAt(offset);
            if (!Character.isWhitespace(codePoint)) return false;
            offset += Character.charCount(codePoint);
        }
        return true;
    }

    private String readLink() {
        return mBinding.link.getText() == null ? "" : mBinding.link.getText().toString();
    }

    private void clearOperation() {
        mOperationId = Long.MIN_VALUE;
        mOperation = -1;
    }

    @Override
    protected void onDestroy() {
        clearOperation();
        Notify.dismiss();
        if (mXray != null) mXray.close();
        super.onDestroy();
    }
}
