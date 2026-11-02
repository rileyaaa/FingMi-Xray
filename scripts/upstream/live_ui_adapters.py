#!/usr/bin/env python3
"""Leanback Xray-only UI overlays on top of 5.8.7 upstream widgets.

Keep official channel selection, recycler payload handling, focus and
accessibility. Suppress already-running remote logo fetches on Xray attach.
"""
from exo_adapters import one


def channel_adapter(s):
    s=one(s,"    private final List<Channel> mItems;",
        """    private final List<Channel> mItems;
    private RecyclerView mRecyclerView;
    private boolean xrayLogoSuppressed;""","channel list Xray logo state")
    s=one(s,"    public void addAll(List<Channel> items) {",
        """    /** Do not let old asynchronous direct logo loads finish after Xray attach. */
    public void setXrayLogoSuppressed(boolean suppressed) {
        if (xrayLogoSuppressed == suppressed) return;
        xrayLogoSuppressed = suppressed;
        if (suppressed && mRecyclerView != null) {
            for (int index = 0; index < mRecyclerView.getChildCount(); index++) {
                RecyclerView.ViewHolder holder =
                        mRecyclerView.getChildViewHolder(mRecyclerView.getChildAt(index));
                if (holder instanceof ViewHolder channelHolder) {
                    Glide.with(channelHolder.binding.logo).clear(channelHolder.binding.logo);
                    channelHolder.binding.logo.setImageDrawable(null);
                }
            }
        }
        notifyDataSetChanged();
    }

    public void addAll(List<Channel> items) {""","channel logo cancellation")
    s=one(s,"        item.loadLogo(holder.binding.logo);",
        """        if (xrayLogoSuppressed) {
            Glide.with(holder.binding.logo).clear(holder.binding.logo);
            holder.binding.logo.setImageDrawable(null);
        } else {
            item.loadLogo(holder.binding.logo);
        }""","logo bind network leak prevention")
    s=one(s,"    @Override\n    public void onViewRecycled(@NonNull ViewHolder holder) {",
        """    @Override
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
    public void onViewRecycled(@NonNull ViewHolder holder) {""",
        "RecyclerView logo holders")
    for marker in ("private void updateSelection(int position, Channel selected)",
                   "notifyItemChanged(position, Boolean.TRUE);",
                   "payloads.stream().allMatch(Boolean.TRUE::equals)",
                   "setXrayLogoSuppressed(boolean suppressed)",
                   "Glide.with(channelHolder.binding.logo).clear(channelHolder.binding.logo)"):
        if marker not in s: raise ValueError("New upstream ChannelAdapter behavior lost: "+marker)
    return s
