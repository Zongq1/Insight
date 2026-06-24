package com.insight.app.feature.insight

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.insight.app.core.domain.usecase.GetInsightsUseCase
import com.insight.app.core.util.NetworkResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class InsightViewModel @Inject constructor(
    private val getInsightsUseCase: GetInsightsUseCase,
) : ViewModel() {

    private val _state = MutableStateFlow(InsightState())
    val state: StateFlow<InsightState> = _state.asStateFlow()

    private val _effect = Channel<InsightEffect>(Channel.BUFFERED)
    val effect = _effect.receiveAsFlow()

    init {
        handleIntent(InsightIntent.LoadInsights)
    }

    fun handleIntent(intent: InsightIntent) {
        when (intent) {
            is InsightIntent.LoadInsights -> loadInsights()
            is InsightIntent.SelectCategory -> selectCategory(intent.category)
            is InsightIntent.DeleteInsight -> deleteInsight(intent.id)
            is InsightIntent.RefreshInsights -> refreshInsights()
            is InsightIntent.NavigateToDetail -> navigateToDetail(intent.insightId)
        }
    }

    private fun navigateToDetail(insightId: String) {
        viewModelScope.launch {
            _effect.send(InsightEffect.NavigateToDetail(insightId))
        }
    }

    private fun loadInsights() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }

            getInsightsUseCase()
                .catch { e ->
                    _state.update { it.copy(isLoading = false, error = e.message) }
                    _effect.send(InsightEffect.ShowSnackbar("加载失败: ${e.message}"))
                }
                .collect { insights ->
                    // 过滤掉已删除的卡片
                    val deletedIds = _state.value.deletedIds
                    val filtered = insights.filter { it.id !in deletedIds }
                    _state.update { it.copy(insights = filtered, isLoading = false) }
                }
        }
    }

    private fun selectCategory(category: String?) {
        _state.update { it.copy(selectedCategory = category) }
    }

    private fun deleteInsight(id: String) {
        viewModelScope.launch {
            // 立即标记为已删除（UI 即时响应）
            _state.update { it.copy(deletedIds = it.deletedIds + id) }
            try {
                getInsightsUseCase.deleteInsight(id)
                _effect.send(InsightEffect.ShowSnackbar("已删除"))
            } catch (e: Exception) {
                // 回滚
                _state.update { it.copy(deletedIds = it.deletedIds - id) }
                _effect.send(InsightEffect.ShowSnackbar("删除失败: ${e.message}"))
            }
        }
    }

    private fun refreshInsights() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, deletedIds = emptySet()) }
            when (val result = getInsightsUseCase.refreshFromNetwork()) {
                is NetworkResult.Success -> {
                    _state.update { it.copy(isLoading = false) }
                }
                is NetworkResult.Error -> {
                    _state.update { it.copy(isLoading = false, error = result.message) }
                    _effect.send(InsightEffect.ShowSnackbar("刷新失败"))
                }
                is NetworkResult.Loading -> {}
            }
        }
    }
}
