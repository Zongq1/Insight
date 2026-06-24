package com.insight.app.feature.detail

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.insight.app.core.domain.model.LogicPoint
import com.insight.app.core.domain.model.Source
import com.insight.app.ui.theme.ConfidenceHigh
import com.insight.app.ui.theme.ConfidenceLow
import com.insight.app.ui.theme.ConfidenceMedium

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InsightDetailScreen(
    insightId: String,
    onNavigateBack: () -> Unit,
    viewModel: InsightDetailViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("洞见详情") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
        ) {
            when {
                state.isLoading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                state.error != null -> {
                    Text(
                        text = state.error ?: "未知错误",
                        modifier = Modifier.align(Alignment.Center),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                state.insight != null -> {
                    InsightDetailContent(insight = state.insight!!)
                }
            }
        }
    }
}

@Composable
private fun InsightDetailContent(
    insight: com.insight.app.core.domain.model.Insight,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
    ) {
        // Category + Confidence
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CategoryChip(category = insight.category)
            ConfidenceIndicator(score = insight.confidenceScore)
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Core Thesis
        Text(
            text = "核心论点",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = insight.coreThesis,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface,
        )

        // Logic Chain
        if (insight.logicChain.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "逻辑链",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(modifier = Modifier.height(8.dp))
            insight.logicChain.forEachIndexed { index, point ->
                LogicChainItem(point = point, index = index + 1)
                if (index < insight.logicChain.lastIndex) {
                    Spacer(modifier = Modifier.height(8.dp))
                }
            }
        }

        // Historical Insight
        insight.historicalInsight?.let { historical ->
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "历史脉络",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = historical,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
            )
        }

        // Sources
        if (insight.sources.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "来源",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(modifier = Modifier.height(8.dp))
            insight.sources.forEach { source ->
                SourceItem(source = source)
                Spacer(modifier = Modifier.height(4.dp))
            }
        }

        // Date
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "生成于: ${insight.dateGenerated}",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
        )
    }
}

@Composable
private fun LogicChainItem(point: LogicPoint, index: Int) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                text = "$index. ${point.premise}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
            )
            Text(
                text = "→ ${point.conclusion}",
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}

@Composable
private fun SourceItem(source: Source) {
    val context = LocalContext.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable {
                try {
                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(source.url)))
                } catch (_: Exception) {}
            }
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = source.name,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.primary,
        )
        Spacer(modifier = Modifier.width(4.dp))
        Text(
            text = source.url,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
            maxLines = 1,
        )
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
    val color = when {
        score >= 0.8f -> ConfidenceHigh
        score >= 0.5f -> ConfidenceMedium
        else -> ConfidenceLow
    }
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
