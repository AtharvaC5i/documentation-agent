"""
metrics_helpers.py

Helper functions to extract metrics from orchestrator results and calculate quality scores.
These functions are called by generate.py to populate the metrics tracker.
"""

import json
from typing import Dict, Any, Tuple, List, Optional


def extract_diagram_metrics(result: Any, diagram_selected: bool = False) -> Dict[str, Any]:
  """
  Extract diagram metrics from orchestrator result.
  Only attempts to extract if diagram was actually selected/requested.
  
  Args:
    result: The generation result object
    diagram_selected: Whether user selected architecture diagram generation
  
  Returns:
    {
      "attempted": bool,
      "success": bool,
      "components_count": int,
      "connections_count": int,
      "expected_components": int,
      "expected_connections": int,
    }
  """
  metrics = {
    "attempted": False,
    "success": False,
    "components_count": 0,
    "connections_count": 0,
    "expected_components": 0,
    "expected_connections": 0,
  }
  
  # If diagram wasn't selected, return all zeros
  if not diagram_selected:
    return metrics
  
  try:
    # Get raw architecture (has diagram components/connections)
    raw_arch = result.get_raw_architecture() if hasattr(result, 'get_raw_architecture') else {}
    if not raw_arch:
      return metrics
    
    metrics["attempted"] = True
    
    # Expected from Core Architecture Step
    expected_comps_list = raw_arch.get("components") or []
    expected_conns_list = raw_arch.get("connections") or []
    if not expected_conns_list and hasattr(result, 'data_flow'):
      expected_conns_list = result.data_flow or []
      
    # Actuals from Diagram Generation Step (Step 2)
    diagram_comps = raw_arch.get("diagram_components")
    if diagram_comps is None:
      diagram_comps = expected_comps_list
      
    diagram_conns = raw_arch.get("diagram_connections")
    if diagram_conns is None:
      diagram_conns = expected_conns_list

    # Match components (case-insensitive)
    expected_names = set()
    for c in expected_comps_list:
      name = c.get("name") or c.get("label") or c.get("id") if isinstance(c, dict) else str(c)
      if name:
        expected_names.add(str(name).strip().lower())
        
    matched_comps = 0
    for c in diagram_comps:
      name = c.get("label") or c.get("id") or c.get("name") if isinstance(c, dict) else str(c)
      if name and str(name).strip().lower() in expected_names:
        matched_comps += 1
      elif name:
        # Check partial match as fallback
        name_clean = str(name).strip().lower()
        if any(name_clean in en or en in name_clean for en in expected_names):
          matched_comps += 1
          
    # Match connections
    expected_conns_set = set()
    expected_id_to_name = {}
    for c in expected_comps_list:
      cid = c.get("id") if isinstance(c, dict) else None
      cname = c.get("name") or c.get("label") if isinstance(c, dict) else str(c)
      if cid:
        expected_id_to_name[str(cid).strip().lower()] = str(cname or cid).strip().lower()
        
    for conn in expected_conns_list:
      if isinstance(conn, dict):
        src = conn.get("source") or conn.get("from")
        tgt = conn.get("target") or conn.get("to")
      else:
        src, tgt = None, None
      if src and tgt:
        src_clean = str(src).strip().lower()
        tgt_clean = str(tgt).strip().lower()
        # Add ID pair
        expected_conns_set.add(frozenset([src_clean, tgt_clean]))
        # Resolve to names and add name pair
        src_name = expected_id_to_name.get(src_clean, src_clean)
        tgt_name = expected_id_to_name.get(tgt_clean, tgt_clean)
        expected_conns_set.add(frozenset([src_name, tgt_name]))
        
    diagram_id_to_name = {}
    for c in diagram_comps:
      if isinstance(c, dict):
        cid = c.get("id")
        cname = c.get("label") or c.get("name")
        if cid:
          diagram_id_to_name[str(cid).strip().lower()] = str(cname or cid).strip().lower()
          
    matched_conns = 0
    for conn in diagram_conns:
      if isinstance(conn, dict):
        src = conn.get("source") or conn.get("from")
        tgt = conn.get("target") or conn.get("to")
      else:
        src, tgt = None, None
      if src and tgt:
        src_clean = str(src).strip().lower()
        tgt_clean = str(tgt).strip().lower()
        
        # Check direct clean match (could be ID-based or name-based)
        if frozenset([src_clean, tgt_clean]) in expected_conns_set:
          matched_conns += 1
          continue
          
        # Check resolved name match
        src_name = diagram_id_to_name.get(src_clean, src_clean)
        tgt_name = diagram_id_to_name.get(tgt_clean, tgt_clean)
        if frozenset([src_name, tgt_name]) in expected_conns_set:
          matched_conns += 1
          continue
          
        # Fallback: check if both endpoints exist in the diagram (partial match)
        if src_clean in diagram_id_to_name or src_name in expected_names:
          if tgt_clean in diagram_id_to_name or tgt_name in expected_names:
            matched_conns += 1

    metrics["components_count"] = matched_comps
    metrics["expected_components"] = len(expected_names) if expected_names else len(diagram_comps)
    metrics["connections_count"] = matched_conns
    metrics["expected_connections"] = len(expected_conns_list) if expected_conns_list else len(diagram_conns)
    
    # Diagram succeeded if actual components and connections were successfully generated and matching
    metrics["success"] = metrics["components_count"] > 0 and len(diagram_comps) > 0
    
  except Exception as e:
    print(f"[Metrics] Warning: failed to extract diagram metrics: {e}")
  
  return metrics


def calculate_quality_scores(result: Any, brd_text: str, tech_doc_text: str, diagram_selected: bool = False) -> Dict[str, float]:
    """
    Calculate quality scores based on generated content.
    
    Args:
        result: The generation result object
        brd_text: Original BRD text
        tech_doc_text: Original technical documentation text
        diagram_selected: Whether diagram generation was attempted
    
    Returns:
        {
            "content_quality": 0.0-1.0,
            "diagram_quality": 0.0-1.0,
            "architecture_alignment": 0.0-1.0,
            "output_validity": 0.0-1.0,
        }
    """
    scores = {
        "content_quality": 0.0,
        "diagram_quality": 0.0,
        "architecture_alignment": 0.0,
        "output_validity": 0.0,
    }
    
    try:
        # Content quality: check if main sections are populated
        has_project = bool(result.project and result.project.name)
        has_arch = bool(result.architecture and result.architecture.pattern)
        has_tech_stack = bool(result.technology_stack and result.technology_stack.frontend)
        has_risks = len(result.risks or []) > 0
        has_roadmap = len(result.roadmap or []) > 0
        
        content_checks = [has_project, has_arch, has_tech_stack, has_risks, has_roadmap]
        scores["content_quality"] = min(1.0, sum(content_checks) / 5.0 * 1.1)  # Allow >100%
        
        # Diagram quality: based on components and connections (only if diagram was selected)
        if diagram_selected:
            raw_arch = result.get_raw_architecture() if hasattr(result, 'get_raw_architecture') else {}
            diagram_comps = raw_arch.get("diagram_components")
            if diagram_comps is None:
                diagram_comps = raw_arch.get("components") or []
            diagram_conns = raw_arch.get("diagram_connections")
            if diagram_conns is None:
                diagram_conns = raw_arch.get("connections") or []
            
            # Ideal: 6-10 components, 8-12 connections
            comp_score = min(1.0, len(diagram_comps) / 8) if diagram_comps else 0.0
            conn_score = min(1.0, len(diagram_conns) / 10) if diagram_conns else 0.0
            scores["diagram_quality"] = round((comp_score * 0.6 + conn_score * 0.4), 3)
        else:
            # If diagram wasn't selected, it's neither good nor bad - neutral score
            scores["diagram_quality"] = 0.0
        
        # Architecture alignment: check if it addresses BRD/TechDoc
        has_problem = bool(result.problem_statement and result.problem_statement.root_cause)
        has_solution = bool(result.proposed_solution and result.proposed_solution.summary)
        has_alignment_goals = len(result.alignment.goals or []) > 0
        
        alignment_checks = [has_problem, has_solution, has_alignment_goals]
        scores["architecture_alignment"] = round(sum(alignment_checks) / 3.0, 3)
        
        # Output validity: assume valid if we got this far (will be verified by PPTX validation)
        scores["output_validity"] = 0.95  # Default; will be set to 1.0 if PPTX passes validation
        
    except Exception as e:
        print(f"[Metrics] Warning: failed to calculate quality scores: {e}")
    
    return scores


def extract_slide_metrics(
    result_dict: Dict[str, Any], 
    selected_slides: Optional[List[str]] = None,
    diagram_success: bool = True
) -> Dict[str, int]:
    """
    Extract slide generation metrics from result dict based on user's selected sections.
    
    Structure:
    - Title template: 2 slides
    - Closing template: 1 slide
    - User-selected sections: add each one
    - Custom slides: add each one
    
    Args:
        result_dict: The generation result as a dict
        selected_slides: List of section names user selected (e.g., ["Title", "Closing", "Diagram", "Solution"])
        diagram_success: Whether the diagram was successfully generated and rendered
    
    Returns:
        {
            "attempted": int,
            "successful": int,
            "failed": int,
            "retry_count": int,
        }
    """
    metrics = {
        "attempted": 0,
        "successful": 0,
        "failed": 0,
        "retry_count": 0,
    }
    
    try:
        # Base: Title (2 slides) + Closing (1 slide) = 3 slides from templates
        slide_count = 3
        
        diagram_selected = False
        
        # If user selected specific sections, count those beyond Title/Closing
        if selected_slides and isinstance(selected_slides, list):
            # Count sections that are NOT Title or Closing (those are already in the base count)
            additional_sections = [
                s for s in selected_slides 
                if s.strip().lower() not in ["title", "closing"]
            ]
            slide_count += len(additional_sections)
            
            diagram_selected = any(
                s.strip().lower() == "diagram"
                for s in additional_sections
            )
            
            # Add custom slides if any
            custom_slides = result_dict.get("custom_slides") or []
            if isinstance(custom_slides, list):
                slide_count += len(custom_slides)
            
            print(f"[Metrics] Slide calculation: 3 (Title 2 + Closing 1) + {len(additional_sections)} selected sections + {len(custom_slides) if custom_slides else 0} custom = {slide_count} total")
        else:
            # Fallback: if no specific selection, count sections that have content
            # This maintains backward compatibility (old behavior when selected_slides not provided)
            slide_count = 3  # Base: Title (2) + Closing (1)
            
            has_alignment = bool(result_dict.get("alignment"))
            has_problem = bool(result_dict.get("problem_statement"))
            has_solution = bool(result_dict.get("proposed_solution"))
            has_arch = bool(result_dict.get("architecture"))
            has_tech = bool(result_dict.get("technology_stack"))
            has_nonfunc = bool(result_dict.get("non_functional"))
            has_roadmap = bool(result_dict.get("roadmap"))
            has_risks = bool(result_dict.get("risks"))
            
            slide_count += sum([
                has_alignment, has_problem, has_solution, has_arch,
                has_tech, has_nonfunc, has_roadmap, has_risks
            ])
            
            arch = result_dict.get("architecture", {})
            diagram_selected = isinstance(arch, dict) and (bool(arch.get("components")) or bool(arch.get("connections")))
            
            # Add custom slides
            custom_slides = result_dict.get("custom_slides") or []
            if isinstance(custom_slides, list):
                slide_count += len(custom_slides)
        
        failed_slides = 0
        if diagram_selected and not diagram_success:
            failed_slides = 1
            
        metrics["attempted"] = slide_count
        metrics["successful"] = max(0, slide_count - failed_slides)
        metrics["failed"] = failed_slides
        metrics["retry_count"] = 0
        
    except Exception as e:
        print(f"[Metrics] Warning: failed to extract slide metrics: {e}")
    
    return metrics


def extract_sections(result_dict: Dict[str, Any], selected_slides: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Extract sections information from the result dict based on user selection.
    
    Args:
        result_dict: The generation result as a dict
        selected_slides: List of section names user selected
    
    Returns:
        {
            "selected_count": int,
            "selected_list": List[str],
            "custom_sections_count": int,
            "custom_sections": List[str],
            "total_sections": int,
        }
    """
    sections_data = {
        "selected_count": 0,
        "selected_list": [],
        "custom_sections_count": 0,
        "custom_sections": [],
        "total_sections": 0,
    }
    
    try:
        # Track selected sections
        if selected_slides and isinstance(selected_slides, list):
            sections_data["selected_count"] = len(selected_slides)
            sections_data["selected_list"] = selected_slides
        
        # Track custom sections
        custom_slides = result_dict.get("custom_slides") or []
        if isinstance(custom_slides, list):
            sections_data["custom_sections_count"] = len(custom_slides)
            custom_titles = []
            for cs in custom_slides:
                if isinstance(cs, dict) and "title" in cs:
                    custom_titles.append(cs["title"])
                elif isinstance(cs, str):
                    custom_titles.append(cs)
            sections_data["custom_sections"] = custom_titles
        
        # Total sections = selected + custom
        sections_data["total_sections"] = (
            sections_data["selected_count"] + sections_data["custom_sections_count"]
        )
        
    except Exception as e:
        print(f"[Metrics] Warning: failed to extract sections: {e}")
    
    return sections_data


def detect_diagram_selected(result_dict: Dict[str, Any]) -> bool:
    """
    Detect if user requested architecture diagram generation.
    Diagram is considered selected if there's an explicit architecture in results.
    
    Args:
        result_dict: The generation result as a dict
    
    Returns:
        bool: True if diagram was generated/attempted
    """
    try:
        # Check if architecture object has components (indicating diagram attempt)
        arch = result_dict.get("architecture", {})
        if isinstance(arch, dict):
            # Check for diagram components or connections
            has_components = bool(arch.get("components"))
            has_connections = bool(arch.get("connections"))
            return has_components or has_connections
        return False
    except Exception as e:
        print(f"[Metrics] Warning: failed to detect diagram selection: {e}")
        return False



def extract_token_usage(response: Any) -> Dict[str, int]:
    """
    Extract token usage from LLM response.
    Handles various response formats from different LLM clients.
    
    Returns:
        {"prompt_tokens": int, "completion_tokens": int}
    """
    try:
        # Check for direct usage object
        if hasattr(response, "usage"):
            usage = response.usage
            return {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
            }
        
        # Check for dict with usage key
        if isinstance(response, dict):
            usage = response.get("usage", {})
            if isinstance(usage, dict):
                return {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                }
        
        # Check for usage in response object as dict
        if isinstance(response, dict) and "usage" in response:
            u = response["usage"]
            if isinstance(u, dict):
                return {
                    "prompt_tokens": u.get("prompt_tokens", 0),
                    "completion_tokens": u.get("completion_tokens", 0),
                }
    except Exception as e:
        print(f"[Metrics] Warning: failed to extract token usage: {e}")
    
    return {"prompt_tokens": 0, "completion_tokens": 0}


def extract_architecture_justification(result: Any) -> Tuple[int, int, int, int]:
    """
    Extract architecture decision justification metrics.
    
    Returns:
        (decisions_identified, decisions_justified, brd_citations, constraint_references)
    """
    decisions_identified = 0
    decisions_justified = 0
    brd_citations = 0
    constraint_references = 0
    
    try:
        # Key decisions that should be present:
        # 1. Architecture pattern
        # 2. Frontend tech choice
        # 3. Backend tech choice
        # 4. AI/ML layer
        # 5. Data storage
        # 6. Hosting/infrastructure
        
        arch = result.architecture or {}
        decisions_identified = sum([
            bool(arch.pattern),
            bool(arch.frontend),
            bool(arch.backend),
            bool(arch.ai_layer),
            bool(arch.data_store),
            bool(arch.hosting),
        ])
        
        # If we have alignment goals, decisions are likely justified
        alignment = result.alignment or {}
        if alignment.goals:
            decisions_justified = decisions_identified
            brd_citations = len(alignment.goals)
        
        # Non-functional requirements = constraints referenced
        nonfunc = result.non_functional or {}
        constraint_references = sum([
            bool(nonfunc.scalability),
            bool(nonfunc.security),
            bool(nonfunc.availability),
            bool(nonfunc.performance),
            bool(nonfunc.compliance),
        ])
        
    except Exception as e:
        print(f"[Metrics] Warning: failed to extract justification metrics: {e}")
    
    return decisions_identified, decisions_justified, brd_citations, constraint_references
