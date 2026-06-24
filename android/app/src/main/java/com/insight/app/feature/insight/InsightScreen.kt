package com.insight.app.feature.insight

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.insight.app.core.domain.model.Insight
import com.insight.app.ui.theme.ConfidenceHigh
import com.insight.app.ui.theme.ConfidenceLow
import com.insight.app.ui.theme.ConfidenceMedium
import kotlinx.coroutines.flow.collectLatest

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InsightScreen(
    viewModel: InsightViewModel = hiltViewModel(),
    onNavigateToDetail: (String) -> Unit = {},
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(Unit) {
        viewModel.effect.collectLatest { effect ->
            when (effect) {
                is InsightEffect.NavigateToDetail -> onNavigateToDetail(effect.insightId)
                is InsightEffect.ShowSnackbar -> snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("洞见") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
                actions = {
                    IconButton(onClick = { viewModel.handleIntent(InsightIntent.RefreshInsights) }) {
                        Icon(Icons.Default.Refresh, contentDescription = "刷新")
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { paddingValues ->
        PullToRefreshBox(
            isRefreshing = state.isLoading && state.insights.isNotEmpty(),
            onRefresh = { viewModel.handleIntent(InsightIntent.RefreshInsights) },
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
        ) {
            when {
                state.isLoading && state.insights.isEmpty() -> {
                    CircularProgressIndicator(
                        modifier = Modifier.align(Alignment.Center),
                    )
                }
                state.error != null && state.insights.isEmpty() -> {
                    Text(
                        text = state.error ?: "未知错误",
                        modifier = Modifier.align(Alignment.Center),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                state.insights.isEmpty() -> {
                    Text(
                        text = "暂无洞见",
                        modifier = Modifier.align(Alignment.Center),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                    )
                }
                else -> {
                    val categories = remember(state.insights) {
                        state.insights.map { it.category }.distinct().sorted()
                    }
                    val filteredInsights = remember(state.insights, state.selectedCategory) {
                        if (state.selectedCategory == null) state.insights
                        else state.insights.filter { it.category == state.selectedCategory }
                    }

                    Column {
                        if (categories.size > 1) {
                            CategoryFilterChips(
                                categories = categories,
                                selectedCategory = state.selectedCategory,
                                onCategorySelected = { category ->
                                    viewModel.handleIntent(
                                        InsightIntent.SelectCategory(
                                            if (category == state.selectedCategory) null else category
                                        )
                                    )
                                },
                            )
                        }
                        InsightList(
                            insights = filteredInsights,
                            onInsightClick = { insightId ->
                                viewModel.handleIntent(InsightIntent.NavigateToDetail(insightId))
                            },
                            onDeleteInsight = { insightId ->
                                viewModel.handleIntent(InsightIntent.DeleteInsight(insightId))
                            },
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun InsightList(
    insights: List<Insight>,
    onInsightClick: (String) -> Unit,
    onDeleteInsight: (String) -> Unit,
) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(
            items = insights,
            key = { it.id },
        ) { insight ->
            val dismissState = rememberSwipeToDismissBoxState(
                confirmValueChange = { value ->
                    if (value == SwipeToDismissBoxValue.EndToStart) {
                        onDeleteInsight(insight.id)
                        true
                    } else {
                        false
                    }
                },
            )

            SwipeToDismissBox(
                state = dismissState,
                backgroundContent = {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .clip(RoundedCornerShape(16.dp))
                            .background(MaterialTheme.colorScheme.error.copy(alpha = 0.1f)),
                        contentAlignment = Alignment.CenterEnd,
                    ) {
                        Icon(
                            Icons.Default.Delete,
                            contentDescription = "删除",
                            tint = MaterialTheme.colorScheme.error,
                            modifier = Modifier.padding(end = 20.dp),
                        )
                    }
                },
                enableDismissFromStartToEnd = false,
                modifier = Modifier.animateItem(),
            ) {
                InsightCard(
                    insight = insight,
                    onClick = { onInsightClick(insight.id) },
                )
            }
        }
    }
}

@Composable
private fun InsightCard(
    insight: Insight,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Top: category + confidence
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CategoryChip(category = insight.category)
                ConfidenceIndicator(score = insight.confidenceScore)
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Core thesis
            Text(
                text = insight.coreThesis,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )

            // Historical insight
            insight.historicalInsight?.let { historical ->
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = historical,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Bottom: source count + date
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    text = "${insight.sources.size} 来源",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                )
                Text(
                    text = insight.dateGenerated,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                )
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun CategoryFilterChips(
    categories: List<String>,
    selectedCategory: String?,
    onCategorySelected: (String) -> Unit,
) {
    FlowRow(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        categories.forEach { category ->
            val isSelected = category == selectedCategory
            FilterChip(
                selected = isSelected,
                onClick = { onCategorySelected(category) },
                label = { Text(category) },
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = MaterialTheme.colorScheme.primaryContainer,
                    selectedLabelColor = MaterialTheme.colorScheme.primary,
                ),
            )
        }
    }
}

@Composable
private fun CategoryChip(category: String) {
    Card(
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer,
        ),
    ) {
        Text(
            text = category,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.primary,
        )
    }
}

@Composable
private fun ConfidenceIndicator(score: Float) {
    val targetColor = when {
        score >= 0.8f -> ConfidenceHigh
        score >= 0.5f -> ConfidenceMedium
        else -> ConfidenceLow
    }
    val color by animateColorAsState(targetValue = targetColor, label = "confidenceColor")
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .clip(CircleShape)
                .background(color),
        )
        Spacer(modifier = Modifier.width(4.dp))
        Text(
            text = "${(score * 100).toInt()}%",
            style = MaterialTheme.typography.labelSmall,
            color = color,
        )
    }
}
