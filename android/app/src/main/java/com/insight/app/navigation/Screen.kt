package com.insight.app.navigation

sealed class Screen(val route: String) {
    data object InsightList : Screen("insight_list")
    data object InsightDetail : Screen("insight_detail/{insightId}") {
        fun createRoute(insightId: String) = "insight_detail/$insightId"
    }
}
