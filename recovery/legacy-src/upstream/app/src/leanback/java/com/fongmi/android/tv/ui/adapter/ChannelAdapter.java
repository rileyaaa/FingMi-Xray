package com.fongmi.android.tv.ui.adapter;

import android.view.LayoutInflater;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.bumptech.glide.Glide;
import com.fongmi.android.tv.bean.Channel;
import com.fongmi.android.tv.databinding.AdapterChannelBinding;

import java.util.ArrayList;
import java.util.List;

public class ChannelAdapter extends RecyclerView.Adapter<ChannelAdapter.ViewHolder> {

    private final OnClickListener mListener;
    private final List<Channel> mItems;
    private RecyclerView mRecyclerView;
    private boolean mXrayLogoSuppressed;

    public ChannelAdapter(OnClickListener listener) {
        mListener = listener;
        mItems = new ArrayList<>();
    }

    public void addAll(List<Channel> items) {
        mItems.clear();
        mItems.addAll(items);
        notifyDataSetChanged();
    }

    public void remove(Channel item) {
        int index = mItems.indexOf(item);
        if (index < 0) return;
        mItems.remove(index);
        notifyItemRemoved(index);
    }

    public void clear() {
        mItems.clear();
        notifyDataSetChanged();
    }

    public Channel get(int position) {
        return mItems.get(position);
    }

    public void setSelected(Channel selected) {
        for (Channel item : mItems) item.setSelected(selected);
        notifyDataSetChanged();
    }

    @Override
    public int getItemCount() {
        return mItems.size();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        return new ViewHolder(AdapterChannelBinding.inflate(LayoutInflater.from(parent.getContext()), parent, false));
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        Channel item = mItems.get(position);
        if (mXrayLogoSuppressed) {
            Glide.with(holder.binding.logo).clear(holder.binding.logo);
            holder.binding.logo.setImageDrawable(null);
        } else {
            item.loadLogo(holder.binding.logo);
        }
        holder.binding.name.setText(item.getShow());
        holder.binding.number.setText(item.getNumber());
        holder.binding.getRoot().setSelected(item.isSelected());
        holder.binding.getRoot().setRightListener(() -> mListener.showEpg(item));
        holder.binding.getRoot().setOnClickListener(v -> mListener.onItemClick(item));
        holder.binding.getRoot().setOnLongClickListener(v -> mListener.onLongClick(item));
    }

    public void setXrayLogoSuppressed(boolean suppressed) {
        if (mXrayLogoSuppressed == suppressed) return;
        mXrayLogoSuppressed = suppressed;

        if (suppressed && mRecyclerView != null) {
            for (int index = 0; index < mRecyclerView.getChildCount(); index++) {
                RecyclerView.ViewHolder holder =
                        mRecyclerView.getChildViewHolder(
                                mRecyclerView.getChildAt(index));
                if (holder instanceof ViewHolder channelHolder) {
                    Glide.with(channelHolder.binding.logo)
                            .clear(channelHolder.binding.logo);
                    channelHolder.binding.logo.setImageDrawable(null);
                }
            }
        }

        notifyDataSetChanged();
    }

    @Override
    public void onAttachedToRecyclerView(@NonNull RecyclerView recyclerView) {
        super.onAttachedToRecyclerView(recyclerView);
        mRecyclerView = recyclerView;
    }

    @Override
    public void onDetachedFromRecyclerView(@NonNull RecyclerView recyclerView) {
        if (mRecyclerView == recyclerView) mRecyclerView = null;
        super.onDetachedFromRecyclerView(recyclerView);
    }

    @Override
    public void onViewRecycled(@NonNull ViewHolder holder) {
        Glide.with(holder.binding.logo).clear(holder.binding.logo);
        holder.binding.logo.setImageDrawable(null);
    }

    public interface OnClickListener {

        void showEpg(Channel item);

        void onItemClick(Channel item);

        boolean onLongClick(Channel item);
    }

    public static class ViewHolder extends RecyclerView.ViewHolder {

        private final AdapterChannelBinding binding;

        ViewHolder(@NonNull AdapterChannelBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }
    }
}
