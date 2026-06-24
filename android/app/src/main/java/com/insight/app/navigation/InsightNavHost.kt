package com.insight.app.navigation

import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.insight.app.feature.insight.InsightScreen

@Composable
fun InsightNavHost(navController: NavHostController) {
    NavHost(
        navController = navController,
        startDestination = Screen.InsightList.route,
    ) {
        composable(Screen.InsightList.route) {
            InsightScreen(
                onNavigateToDetail = { insightId ->
                    navController.navigate(Screen.InsightDetail.createRoute(insightId))
                },
            )
        }

        composable(
            route = Screen.InsightDetail.route,
            arguments = listOf(
                navArgument("insightId") { type = NavType.StringType },
            ),
            enterTransition = { slideInHorizontally { it } },
            exitTransition = { slideOutHorizontally { it } },
            popEnterTransition = { slideInHorizontally { -it } },
            popExitTransition = { slideOutHorizontally { it } },
        ) { backStackEntry ->
            val insightId = backStackEntry.arguments?.getString("insightId") ?: return@composable
            com.insight.app.feature.detail.InsightDetailScreen(
                insightId = insightId,
                onNavigateBack = { navController.popBackStack() },
            )
        }
    }
}
