package com.insight.app.feature.detail

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.insight.app.core.domain.model.Insight
import com.insight.app.core.domain.usecase.GetInsightsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class InsightDetailState(
    val insight: Insight? = null,
    val isLoading: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class InsightDetailViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val getInsightsUseCase: GetInsightsUseCase,
) : ViewModel() {

    private val insightId: String = savedStateHandle["insightId"] ?: ""

    private val _state = MutableStateFlow(InsightDetailState())
    val state: StateFlow<InsightDetailState> = _state.asStateFlow()

    init {
        loadInsight()
    }

    private fun loadInsight() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            try {
                val insight = getInsightsUseCase.getInsightById(insightId)
                if (insight != null) {
                    _state.update { it.copy(insight = insight, isLoading = false) }
                } else {
                    _state.update { it.copy(isLoading = false, error = "Insight not found") }
                }
            } catch (e: Exception) {
                _state.update { it.copy(isLoading = false, error = e.message) }
            }
        }
    }
}
