package com.fongmi.android.tv.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;

import androidx.viewbinding.ViewBinding;

import com.fongmi.android.tv.xray.legacy.LegacyXrayErrorSanitizer;
import com.fongmi.android.tv.xray.legacy.LegacyXrayOperation;
import com.fongmi.android.tv.xray.legacy.LegacyXraySettingsController;
import com.fongmi.android.tv.xray.legacy.LegacyXrayShareLinkNormalizer;
import com.fongmi.android.tv.R;
import com.fongmi.android.tv.databinding.ActivitySettingXrayBinding;
import com.fongmi.android.tv.event.XrayImportEvent;
import com.fongmi.android.tv.ui.base.BaseActivity;
import com.fongmi.android.tv.utils.Notify;

import org.greenrobot.eventbus.Subscribe;
import org.greenrobot.eventbus.ThreadMode;

public final class SettingXrayActivity extends BaseActivity
        implements LegacyXraySettingsController.Listener {

    private ActivitySettingXrayBinding mBinding;
    private LegacyXraySettingsController mXray;
    private long mOperationId = Long.MIN_VALUE;
    private int mOperation = -1;
    private String mTestLink = "";
    private boolean mTestUdp;

    public static void start(Activity activity) {
        activity.startActivity(new Intent(activity, SettingXrayActivity.class));
    }

    @Override
    protected ViewBinding getBinding() {
        return mBinding = ActivitySettingXrayBinding.inflate(getLayoutInflater());
    }

    @Override
    protected void initView(Bundle savedInstanceState) {
        mXray = new LegacyXraySettingsController(this, this);
        mBinding.udpSwitch.setChecked(mXray.isUdpEnabled());
        try {
            mBinding.link.setText(mXray.getShareLink());
            mBinding.link.setSelection(mBinding.link.length());
        } catch (Exception error) {
            Notify.show(LegacyXrayErrorSanitizer.fromException(error));
        }
        mBinding.link.requestFocus();
    }

    @Override
    protected void initEvent() {
        mBinding.udp.setOnClickListener(this::onUdp);
        mBinding.save.setOnClickListener(this::onSave);
        mBinding.test.setOnClickListener(this::onTest);
        mBinding.phone.setOnClickListener(this::onPhone);
        mBinding.delete.setOnClickListener(this::onDelete);
    }

    private void onUdp(View view) {
        mBinding.udpSwitch.setChecked(!mBinding.udpSwitch.isChecked());
    }

    private void onSave(View view) {
        if (mOperation == LegacyXrayOperation.RESET_SECURITY) return;
        try {
            mXray.save(readLink(), mBinding.udpSwitch.isChecked());
            Notify.show(R.string.xray_saved);
        } catch (Exception error) {
            Notify.show(LegacyXrayErrorSanitizer.fromException(error));
        }
    }

    private void onTest(View view) {
        if (mOperationId != Long.MIN_VALUE) return;
        try {
            mTestLink = LegacyXrayShareLinkNormalizer.normalize(readLink());
            mTestUdp = mBinding.udpSwitch.isChecked();
            Notify.progress(getActivity());
            mOperation = LegacyXrayOperation.TEST;
            mOperationId = mXray.test(mTestLink, mTestUdp);
        } catch (Exception error) {
            clearOperation();
            Notify.dismiss();
            Notify.show(LegacyXrayErrorSanitizer.fromException(error));
        }
    }

    private void onPhone(View view) {
        PushActivity.start(this, 6);
    }

    private void onDelete(View view) {
        if (mOperationId != Long.MIN_VALUE) return;
        try {
            Notify.progress(getActivity());
            mBinding.link.setText("");
            mBinding.udpSwitch.setChecked(false);
            mOperation = LegacyXrayOperation.RESET_SECURITY;
            mOperationId = mXray.delete();
        } catch (Exception error) {
            clearOperation();
            Notify.dismiss();
            Notify.show(LegacyXrayErrorSanitizer.fromException(error));
        }
    }

    @Override
    public void onResult(
            long operationId,
            int operation,
            boolean success,
            long latencyMs,
            String message) {
        if (operationId != mOperationId) return;

        int finishedOperation = mOperation;
        clearOperation();
        Notify.dismiss();

        if (finishedOperation == LegacyXrayOperation.TEST && !testInputUnchanged()) {
            Notify.show(R.string.xray_changed_retry);
            return;
        }

        if (!success) {
            Notify.show(message);
            return;
        }

        if (finishedOperation == LegacyXrayOperation.RESET_SECURITY) {
            Notify.show(R.string.xray_deleted);
        } else if (finishedOperation == LegacyXrayOperation.TEST) {
            Notify.show(getString(R.string.xray_test_success, latencyMs));
        }
    }

    private boolean testInputUnchanged() {
        try {
            return LegacyXrayShareLinkNormalizer.normalize(readLink()).equals(mTestLink)
                    && mBinding.udpSwitch.isChecked() == mTestUdp;
        } catch (Exception ignored) {
            return false;
        }
    }

    @Subscribe(threadMode = ThreadMode.MAIN)
    public void onXrayImportEvent(XrayImportEvent event) {
        if (event == null || event.link() == null || event.link().isBlank()) return;

        if (mOperationId != Long.MIN_VALUE && mOperation != LegacyXrayOperation.RESET_SECURITY) {
            // Final APK abandons the old settings Binder generation on phone
            // import rather than remotely cancelling the native operation.
            mXray.abandon();
            clearOperation();
            Notify.dismiss();
        }

        String link = event.link().trim();
        mBinding.link.setText(link);
        mBinding.link.setSelection(mBinding.link.length());
        Notify.show(R.string.xray_phone_received);
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
