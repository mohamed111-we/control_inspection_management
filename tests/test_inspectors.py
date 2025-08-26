from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError, ValidationError,UserError
from datetime import date, timedelta


@tagged('post_install', '-at_install', 'inspection_management')
class TestInspectionModels(TransactionCase):
    def setUp(self):
        super(TestInspectionModels, self).setUp()

        # Setup groups
        self.inspection_manager_group = self.env.ref('control_inspection_management.group_inspection_manager')
        self.user_group = self.env.ref('base.group_user')

        # Setup users
        self.test_manager = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'groups_id': [(6, 0, [
                self.inspection_manager_group.id,
                self.user_group.id
            ])],
        })

        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'groups_id': [(6, 0, [self.user_group.id])],
        })

        # Setup test data
        self.test_employee = self.env['hr.employee'].create({
            'name': 'Test Inspector',
            'department_id': self.env.ref('hr.dep_rd').id,
        })

        self.test_plan = self.env['inspection.plan'].create({
            'name': 'Test Plan',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=7),
        })

        self.test_visit = self.env['inspection.visit'].create({
            'name': 'Test Visit',
            'target_entity': 'Test Entity',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=1),
            'plan_id': self.test_plan.id,
            'inspector': self.test_employee.id,
        })

        self.test_penalty = self.env['inspection.penalties'].create({
            'name': 'Test Penalty',
            'type': 'fine',
            'status': 'issued',
            'amount': 100.0,
        })

        self.test_violation = self.env['inspection.violations'].create({
            'name': 'Test Violation',
        })

    # ========== Inspector Tests ==========
    @tagged('inspectors')
    def test_01_create_inspector(self):
        """Test creating an inspector with valid data."""
        inspector = self.env['inspection.inspector'].create({
            'name': self.test_employee.id,
        })

        self.assertEqual(inspector.name, self.test_employee, "Inspector name should match the employee.")
        self.assertEqual(inspector.department_id, self.test_employee.department_id,
                         "Department should match the employee's department.")
        self.assertTrue(inspector.is_active, "Inspector should be active by default.")

    @tagged('inspectors', 'security')
    def test_02_inspector_access_control(self):
        """Test access control for inspectors."""
        # Test manager can create
        self.env = self.env(user=self.test_manager)
        inspector = self.env['inspection.inspector'].create({
            'name': self.test_employee.id,
        })
        self.assertTrue(inspector, "Inspection Manager should be able to create an inspector.")

        # Test regular user cannot create
        self.env = self.env(user=self.test_user)
        with self.assertRaises(AccessError):
            self.env['inspection.inspector'].create({
                'name': self.test_employee.id,
            })

    # ========== Inspection Plan Tests ==========
    @tagged('inspection_plan')
    def test_03_create_plan(self):
        """Test creating an inspection plan with valid data."""
        plan = self.env['inspection.plan'].create({
            'name': 'New Test Plan',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
        })

        self.assertEqual(plan.status, 'draft', "New plan should be in draft status")
        self.assertEqual(plan.visits_count, 0, "New plan should have 0 visits")

    @tagged('inspection_plan', 'validation')
    def test_04_plan_date_validation(self):
        """Test date validation for inspection plans."""
        with self.assertRaises(ValidationError):
            self.env['inspection.plan'].create({
                'name': 'Invalid Plan',
                'start_date': date.today(),
                'end_date': date.today() - timedelta(days=1),  # End before start
            })

    @tagged('inspection_plan', 'security')
    def test_05_plan_access_control(self):
        """Test access control for inspection plans."""
        # Test manager can create
        self.env = self.env(user=self.test_manager)
        plan = self.env['inspection.plan'].create({
            'name': 'Manager Plan',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=7),
        })
        self.assertTrue(plan, "Inspection Manager should be able to create a plan.")

        # Test regular user can also create (adjust based on your security requirements)
        self.env = self.env(user=self.test_user)
        plan = self.env['inspection.plan'].create({
            'name': 'User Plan',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=7),
        })
        self.assertTrue(plan, "Regular user should be able to create a plan.")

    # ========== Inspection Visit Tests ==========
    @tagged('inspection_visit')
    def test_06_create_visit(self):
        """Test creating an inspection visit with valid data."""
        visit = self.env['inspection.visit'].create({
            'name': 'New Visit',
            'target_entity': 'New Entity',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=1),
            'plan_id': self.test_plan.id,
            'inspector': self.test_employee.id,
        })

        self.assertEqual(visit.status, 'new', "New visit should be new")
        self.assertEqual(self.test_plan.visits_count, 2, "Plan should now have 2 visits")

    @tagged('inspection_visit', 'validation')
    def test_07_visit_validation(self):
        """Test validation rules for inspection visits."""
        # Test name length validation
        with self.assertRaises(ValidationError):
            self.env['inspection.visit'].create({
                'name': 'A' * 101,  # Exceeds 100 characters
                'target_entity': 'Test Entity',
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=1),
                'plan_id': self.test_plan.id,
                'inspector': self.test_employee.id,
            })

        # Test date validation
        with self.assertRaises(ValidationError):
            self.env['inspection.visit'].create({
                'name': 'Invalid Date Visit',
                'target_entity': 'Test Entity',
                'start_date': date.today(),
                'end_date': date.today() - timedelta(days=1),
                'plan_id': self.test_plan.id,
                'inspector': self.test_employee.id,
            })

    @tagged('inspection_visit', 'security')
    def test_08_visit_status_restrictions(self):
        """Test status-based restrictions on visits."""
        # Test editing completed visit
        self.test_visit.write({'status': 'completed'})
        with self.assertRaises(UserError):
            self.test_visit.write({'name': 'Updated Name'})

        # Test deleting completed visit
        with self.assertRaises(UserError):
            self.test_visit.unlink()

    # ========== Penalties Tests ==========
    @tagged('penalties')
    def test_09_create_penalty(self):
        """Test creating a penalty with valid data."""
        penalty = self.env['inspection.penalties'].create({
            'name': 'New Penalty',
            'type': 'warning',
            'status': 'issued',
            'amount': 50.0,
        })

        self.assertEqual(penalty.status, 'issued', "New penalty should be issued")
        self.assertEqual(penalty.type, 'warning', "Penalty type should be waring")


    @tagged('penalties', 'security')
    def test_11_penalty_access_control(self):
        """Test access control for penalties."""
        # Test manager can create
        self.env = self.env(user=self.test_manager)
        penalty = self.env['inspection.penalties'].create({
            'name': 'Manager Penalty',
            'type': 'fine',
            'status': 'issued',
            'amount': 100.0,
        })
        self.assertTrue(penalty, "Inspection Manager should be able to create a penalty.")

        self.env = self.env(user=self.test_user)
        with self.assertRaises(AccessError):
            self.env['inspection.penalties'].create({
                'name': 'User Penalty',
                'type': 'fine',
                'status': 'issued',
                'amount': 100.0,
            })

    # ========== Violations Tests ==========
    @tagged('violations')
    def test_12_create_violation(self):
        """Test creating a violation with valid data."""
        violation = self.env['inspection.violations'].create({
            'name': 'New Violation',
        })
        self.assertEqual(violation.name, 'New Violation', "Violation name should match")


    @tagged('violations', 'search')
    def test_13_violation_search(self):
        """Test searching for violations."""
        search_result = self.env['inspection.violations'].search([('name', 'ilike', 'Test')])
        self.assertEqual(len(search_result), 1, "Should find one violation")
        self.assertEqual(search_result.id, self.test_violation.id, "Should find the test violation")

    # ========== Cross-Model Tests ==========
    @tagged('integration')
    def test_14_plan_visit_relationship(self):
        """Test the relationship between plans and visits."""
        # Create a new plan with visits
        plan = self.env['inspection.plan'].create({
            'name': 'Integration Test Plan',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=14),
        })

        visit1 = self.env['inspection.visit'].create({
            'name': 'Integration Visit 1',
            'target_entity': 'Entity A',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=1),
            'plan_id': plan.id,
            'inspector': self.test_employee.id,
        })

        visit2 = self.env['inspection.visit'].create({
            'name': 'Integration Visit 2',
            'target_entity': 'Entity B',
            'start_date': date.today() + timedelta(days=7),
            'end_date': date.today() + timedelta(days=8),
            'plan_id': plan.id,
            'inspector': self.test_employee.id,
        })

        # Test the relationship
        self.assertEqual(len(plan.planned_visits_ids), 2, "Plan should have 2 visits")
        self.assertEqual(plan.visits_count, 2, "Visit count should be 2")
        self.assertEqual(visit1.plan_id, plan, "Visit 1 should belong to the plan")
        self.assertEqual(visit2.plan_id, plan, "Visit 2 should belong to the plan")