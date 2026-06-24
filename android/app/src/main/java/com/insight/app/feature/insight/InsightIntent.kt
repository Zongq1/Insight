package com.insight.app.feature.insight

sealed interface InsightIntent {
    data object LoadInsights : InsightIntent
    data class SelectCategory(val category: String?) : InsightIntent
    data class DeleteInsight(val id: String) : InsightIntent
    data object RefreshInsights : InsightIntent
    data class NavigateToDetail(val insightId: String) : InsightIntent
}
