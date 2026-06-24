package com.insight.app.feature.insight

sealed interface InsightEffect {
    data class ShowSnackbar(val message: String) : InsightEffect
    data class NavigateToDetail(val insightId: String) : InsightEffect
}
